# Copyright (c) 2023 by Microsoft Corporation.
# Licensed under the MIT license.


from typing import Optional, List, Set
from dataclasses import dataclass

from parrot.exceptions import ParrotCoreUserError
from parrot.utils import get_logger, RecyclePool

from parrot.serve.graph import RequestChain
from parrot.serve.backend_repr import ExecutionEngine
from parrot.serve.backend_repr.model import get_model_type, ModelType

from ..engine_manager import EngineManager
from ..context_manager import ServeCoreContextManager
from .completion_task import CompletionTask, TaskStatus


logger = get_logger("GlobalScheduler")

MAX_DELAY_THRESHOLD = 10
@dataclass
class GlobalSchedulerConfig:
    app_fifo: bool = False
    graph_group: bool = False
    ctx_group: bool = False
    ctx_aware: bool = False
    max_queue_size: int = 1024
    delayCounterThreshold: int = 100
    

class GlobalScheduler:
    """GlobalScheduler (GS) solves the task scheduling problem in the global scope."""

    def __init__(
        self,
        config: GlobalSchedulerConfig,
        engine_mgr: EngineManager,
        context_mgr: ServeCoreContextManager,
    ):
        # ---------- Basic ----------
        self.config = config
        self.engine_mgr = engine_mgr
        self.context_mgr = context_mgr

        # ---------- Task Queue ----------
        self.task_queue: List[CompletionTask] = []
        self.bad_scheduled = 0
        self.impossible_scheduled = 0
        self.total_scheduled = 0
        # bad, impossible(new prefix), good
        # good / total

    def _get_engine_list(
        self,
        tasks: List[CompletionTask],
        tasks_num_upperbound: int,
    ) -> List[ExecutionEngine]:
        engine_list = self.engine_mgr.get_live_engines()    

        # NOTE(chaofan): Suppose all tasks noted the same "models" arg.
        models = tasks[0].chain.metadata.models
        model_type_str = tasks[0].chain.metadata.model_type
        model_type = get_model_type(model_type_str)
        # TODO(chaofan): Throughput/latency criteria

        def check_engine_available(engine: ExecutionEngine):
            # Check whether the mode type matches
            if model_type != engine.model.model_type:
                return False

            # Check whether the model matches
            if len(models) > 0 and engine.model_name not in models:
                return False

            # Check whether it violates the tasks_num_upperbound of the tasks.
            # NOTE(chaofan): For TaskGroup (i.e. tasks passed to this function),
            # the whole group is considered as a single task.
            if 1 + engine.get_num_tasks() > 6:
                return False

            # Check whether it violates the tasks_num_upperbound of the engine.
            if len(tasks) + engine.get_num_tasks() > 6:
                return False

            # Check whether the engine has enough task capacity.
            if len(tasks) > engine.get_remain_tasks_capacity():
                return False

            if model_type == ModelType.TOKEN_ID:
                total_tokens_num = 0
                for task in tasks:
                    total_tokens_num += task.get_token_nums(engine.model.tokenizer_name)

                # Check whether the engine has enough token capacity.
                if total_tokens_num > engine.get_remain_tokens_capacity():
                    return False

            return True
        toret = [engine for engine in engine_list if check_engine_available(engine)]
        toret.sort(key=lambda x: x.get_num_tasks())
        print("Engines Availabe", [x.engine_id for x in toret])
        
        return toret

    def _find_engine(self, tasks: List[CompletionTask]) -> None:
        """Find the best engine for a group of tasks."""

        tasks_num_upperbound = 999999999
        for task in tasks:
            tasks_num_upperbound = min(
                tasks_num_upperbound, task.schedule_annotation.tasks_num_upperbound
            )

        # Get the engine list
        engine_list = self._get_engine_list(tasks, tasks_num_upperbound)

        if len(engine_list) == 0:
            return

        # if len(engine_list) == 0:
        #     if len(tasks) == 1:
        #         return
        #     else:
        #         # Split the group
        #         for task in tasks:
        #             self._find_engine([task])
        #         return

        # Get the engines with Context
        # We use the first task's context to find the engines with the same context
        engine_ids_with_prefixes = []
        if self.config.ctx_aware:
            engine_ids_with_prefixes = self.context_mgr.query_prefixes_in_engines(
                tasks[0]
            )
        # [same context, sameprefix] ["a{}", "bbbb{}", "c{}"] ->taask group if you do graph group enabled,   {1:[a], 2:[a,bbbb]}
        # print(engine_ids_with_prefixes)
        # COMMENT: see you can improve the task[0] thing, 
        # or match it to biggest prefix, also measuere impossible
        # print(engine_ids_with_prefixes)
        # from the ready engines, check which has a prefix
        # just put it in the one with best prefix, and let it scheddule it later - by setting delay parameter to a 10000000
        # 3 req prefix a, 1 req prefix a 
        # same capacity, same load
        # do you want to build sticky machines, 
        # how do you balance stickyness 
        # dag optimizations, ask moshi or search it up
        # throughput vs latency, vy controlling batchsize on diff machiens

        best_engine = None
        max_counter = max(task.delay_counter for task in tasks)
        optimal_engine_found = False
        for engine in engine_list:
            if best_engine is None:
                best_engine = engine
                if self.config.ctx_aware and engine.engine_id in engine_ids_with_prefixes:
                    optimal_engine_found = True
            elif (
                self.config.ctx_aware
                and engine.engine_id in engine_ids_with_prefixes
                and best_engine.engine_id not in engine_ids_with_prefixes):
            #) or engine.get_num_tasks() == 0:
                # Context-aware engine is preferred
                best_engine = engine
                optimal_engine_found = True
            else:
                # Select the best engine (minimizing the negative impacts, i.e. minimizing the decreasing of upperbound)
                # If the upperbound is not affected, select the engine with the most capacity.
                if (
                    engine.get_tasks_num_upperbound()
                    < best_engine.get_tasks_num_upperbound()
                ):
                    best_engine = engine
                elif (
                    engine.get_remain_tokens_capacity()
                    < best_engine.get_remain_tokens_capacity()
                ):
                    best_engine = engine
        # print("engine id with prefix", engine_ids_with_prefixes)
        if False and MAX_DELAY_THRESHOLD > max_counter and not optimal_engine_found and engine_ids_with_prefixes:
            for task in tasks:
                # print("DELAYING")
                task.delay_counter += 1
            return 
        elif max_counter == MAX_DELAY_THRESHOLD:
            print("Group was delayed too much")

 
        # Dispatch the tasks to the engine
        assert best_engine is not None
        #print("Scheduled on: ", best_engine.engine_id)
        for task in tasks:
            task.schedule_to(best_engine)
        self.total_scheduled += len(tasks)
        if not optimal_engine_found:
            self.bad_scheduled += len(tasks)
        print("BAD SCHEDULED COUNT", self.bad_scheduled, self.total_scheduled)  
    # ---------- Public Methods ----------

    def submit_task(self, task: CompletionTask) -> None:
        """Submit a task to the scheduler's queue."""

        if len(self.task_queue) >= self.config.max_queue_size:
            raise ParrotCoreUserError(
                RuntimeError(
                    f"Task queue is full. Current size: {len(self.task_queue)}. "
                    f"Hence the incoming task is rejected."
                )
            )

        logger.debug(
            f"Session(session_id={task.chain.session_id}) submit Task(task_id={task.task_id})"
            " to GlobalScheduler."
        )

        self.task_queue.append(task)
        task.status = TaskStatus.INQUEUE
        return

    def schedule(self) -> None:
        """Try to schedule all tasks in scheduler's queue."""

        if self.config.app_fifo:
            # Sort the tasks by the order of depth
            # The deeper the chain, the higher the priority
            self.task_queue.sort(key=lambda x: -x.chain.gen_node.sv.depth)

        # NOTE(chaofan): The tasks are sorted by priority, by default.
        for i, task in enumerate(self.task_queue):
            if task.is_scheduled:
                continue

            # Group tasks in rest queue
            cur_group: List[CompletionTask] = [task]
            chain_groups = set(task.chain.chain_groups)

            # Only allow one type of grouping at a time
            graph_group_enabled = self.config.graph_group
            ctx_group_enabled = self.config.ctx_group

            if graph_group_enabled or ctx_group_enabled:
                for j in range(i + 1, len(self.task_queue)):
                    task_j = self.task_queue[j]

                    # TODO(chaofan): Models match check
                    models_i = task.chain.metadata.models
                    models_j = task_j.chain.metadata.models

                    # TODO(chaofan): Criteria match check. Only group tasks with the same criteria.

                    MAX_GROUP_LEN = 6
                    if graph_group_enabled:
                        chain_groups_j = set(task_j.chain.chain_groups)
                        common_groups = chain_groups.intersection(chain_groups_j)
                        if len(common_groups) > 0:
                            if len(cur_group) < MAX_GROUP_LEN:
                                cur_group.append(task_j)
                                chain_groups = common_groups
                                ctx_group_enabled = False  # Use graph group this round

                    # Context group check
                    if ctx_group_enabled:
                        if task.chain.first_node.sv == task_j.chain.first_node.sv:
                            if len(cur_group) < MAX_GROUP_LEN:
                                cur_group.append(task_j)
                                graph_group_enabled = False  # Use context group this round


            # Try to find engines for the group
            self._find_engine(cur_group)
            # 3 summarzers
            # 1
            #
            '''
            asd
            asdfadsfasdf
            10 summarizer tasks -> togther, on throughput machine

            1 final summarizer task based on input of prev 10, on some latency machine, but after the 

            once you delay something, set/dict
            next schedule gets called
            [dealyed, new, new, new]
            [ l........]
            [[d1, n1, d2], ...]
            dict task : delayed counter
            
            max counter

            '''
        # Update the task queue
        prev_task_queue = self.task_queue
        scheduled_task = [task for task in prev_task_queue if task.is_scheduled]
        self.task_queue = [task for task in prev_task_queue if not task.is_scheduled]

        # Display the scheduled results.
        # NOTE(chaofan): Only display >0 case to reduce the log size.
        if len(scheduled_task) > 0:
            logger.debug(
                f"Scheduled {len(scheduled_task)} tasks. Results: \n"
                + "\n".join(
                    [
                        f"  Task {task.task_id} -> engine: id={task.engine.engine_id}, name={task.engine.name}, "
                        f"num_tasks={task.engine.get_num_tasks()}, "
                        f"remain_tasks_capacity={task.engine.get_remain_tasks_capacity()}, "
                        f"remain_tokens_capacity={task.engine.get_remain_tokens_capacity()}, "
                        f"tasks_num_upperbound={task.engine.get_tasks_num_upperbound()}, "
                        f"tokens_num={task.engine.get_tokens_num()}, "
                        for task in scheduled_task
                    ]
                )
            )

        return
    



# We are in the process of testing our delay scheduling changes that are meant to increase data locality for prefix sharing but we wanted your suggestions on any general DAG scheudling optimizations we could try for parrot? 
# We feel there might be more avenues to optimize end to end request through DAG based optimization, but were wondering what kind of optimizations we might be able to look into for this?
    '''
    Split up group if graph group enabled in find engine, since for graph group it doesn't need to run on same engine, it just needs to finish at same time
    Do both context and graph group enabled


    {keshav ideas}:
    Implement other scheduling principles at higher level:
    1). We are looking at delay scheduling right now. We should think about our change carefully and see how effective this will be
        and how it fits into the code. We can also look into other ways to implement delay scheduling.
    2). We can build some notion of fairness or maybe QOE (second one is way harder) for end-to-end application. Previous works focus on 
        request level fairness but we do not care about that I think. Also might be interesting to look into starvation, but that might have 
        less scope.

    chain style - so previously we had task group and context scheduling but now we have chain -group


    aryan
    do they even do performance criteria scheduling
    eary summary throughput
    what is graph group, is it one task group or the same query

    could it be good to split task groups
    since you are fine with delaying the tasks that are earlier in the chain, can you make those throughput requests

    -interleaved is bad?? 
    task group, context


    (A) -> b -> d -> c -> d : latency
    x ->latency

    b -> d -> c -> d -> throughput
    y  ->throughput

    ------------- next round
    b -> d -> c ->
    y -> free latecy machine because u didnt put A on it
    -----------------------------
    if throughput is 1 can look at context group

    if current group is too big, too many input tokens, to calculate this - only count shared prefixes once

    split up your task group so things go on machines with context


    a - b ->c ->d
            x  -> dis time long as hell -> d
            y -> d
            z -> d
            w -> d

    a - b ->c ->d
        z    x  -> dis time long as hell -> d
        w    y -> d
            

    huge database async

    small call

    chat things were small input large output
    summarization large input small output
    coding is large input small output

    ask moshi about other dag optimizatino cuz he said he invented parrot and did dag stuff 
    look into batch size stuff
    look into how to detect prefix sharing


    '''