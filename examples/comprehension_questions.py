from parrot import P

vm = P.VirtualMachine(
    core_http_addr="http://localhost:9000",
    mode="debug",
)



@P.semantic_function(formatter=P.allowing_newline)
def Passage1(question:P.Input, response: P.Output):
    """Role: You are a high school student answering questions for an english class. Read the passage below and answer the subsequent question.

    Passage: 
    One afternoon I made chicharrones and carried them over to Celia's apartment. She clapped her hands together in delight when she saw me and motioned for me to come inside. “These are for you,” I said, holding out a foilcovered plate. She lifted a corner of the foil and sniffed. “Sabroso,” she said. I loved how full her home felt, embroidered pillows on the couches, a curio stacked with milk glass bowls and recuerdos and folded tablecloths, red votives along the windowsills, spidery potted plants, woven rugs, unframed posters of Panamá beaches on the walls, a box of rinsed bottles on the floor, a small radio on top of the refrigerator, a plastic bag filled with garlic hanging from a doorknob, a collection of spices clustered on a platter on the counter. The great accumulation of things almost hid the cracks in the walls and the stains on the floor and the scratches that clouded the windows. “Mi casa es tu casa,” Celia joked as I looked around. “Isn't that what the Americans say?” She poured cold, crackling Coca-Colas for both of us, and we sat on the couch, sipping them and taking small bites of the chicharrones. She looked just as she had the first time I met her: impeccably pulled together, with a face full of makeup, fuchsia lips, chestnut-brown chin-length hair curled at the ends and tucked neatly behind her ears, small gold earrings. So unlike most of my friends at home, who used nothing but soap on their faces and aloe on their hands and who kept their hair pulled into ponytails, like mine, or simply combed after it had been washed and left to air-dry. Celia told me about the provisions we would need for winter—heavy coats and a stack of comforters and something called long underwear that made me laugh when she tried to describe it—and about a place called the Community House where they offered immigrant services if we needed them. She gossiped about people in the building. She told me that Micho Alvarez, who she claimed always wore his camera around his neck, had a sensitive side, despite the fact that he might look big and burly, and that Benny Quinto, who was close friends with Micho, had studied to be a priest years ago. She said that Quisqueya dyed her hair, which was hardly news—I had assumed as much when I met her. “It's the most unnatural shade of red,” Celia said. “Rafael says it looks like she dumped a pot of tomato sauce on her head.” She chortled. “Quisqueya is a busybody, but it's only because she's so insecure. She doesn't know how to connect with people. Don't let her put you off.” Celia began telling me about when she and Rafael and her boys had come here from Panamá, fifteen years ago, after the invasion. “So your son, he was born there?” I asked.

    “I have two boys,” she said. “Both of them were born there. Enrique, my oldest, is away at college on a soccer scholarship. And there's Mayor, who you met. He's nothing at all like his brother. Rafa thinks we might have taken the wrong baby home from the hospital.” She forced a smile. “Just a joke, of course.” She stood and lifted a framed picture from the end table. “This is from last summer before Enrique went back to school,” she said, handing it to me. “Micho took it for us.” In the photo were two boys: Mayor, whom I recognized from the store, small for his age with dark, buzzed hair and sparkling eyes, and Enrique, who stood next to his brother with his arms crossed, the faint shadow of a mustache above his lip. “What about you?” Celia asked. “Do you have other children besides your daughter?” “Only her,” I said, glancing at my hands around the glass. The perspiration from the ice had left a ring of water on the thigh of my pants. “And she's going . . .” Celia trailed off, as though she didn't want to say it out loud. “To Evers.” Celia nodded. She looked like she didn't know what to say next, and I felt a mixture of embarrassment and indignation. “It's temporary,” I said. “She only has to go there for a year or two.” “You don't have to explain it to me.” “She's going to get better.” “I've heard it's a good school.” “I hope so. It's why we came.” Celia gazed at me for a long time before she said, “When we left Panamá, it was falling apart. Rafa and I thought it would be better for the boys to grow up here. Even though Panamá was where we had spent our whole lives. It's amazing, isn't it, what parents will do for their children?” She put her hand on mine. A benediction. From then, we were friends


    Question: {{question}} 

    Response format:
    
    ```{{response}}```
    """

@P.semantic_function(formatter=P.allowing_newline)
def Passage2(question:P.Input, response: P.Output):
    """Role: You are a high school student answering questions for an english class. Read the passage below and answer the subsequent question.

    Passage: 
    Voters need to understand the prosaic details of complex policies. Most have staked out positions on these issues, but they are not often reasoned positions, which take hard intellectual work. Most citizens opt instead for simplistic explanations, assuming wrongly that they comprehend the nuances of issues. Psychological scientists have a name for this easy, automatic, simplistic thinking: the illusion of explanatory depth. We strongly believe that we understand complex matters, when in fact we are clueless, and these false and extreme beliefs shape our preferences, judgments, and actions— including our votes. Is it possible to shake such deep-rooted convictions? That's the question that Philip Fernbach, a psychological scientist at the University of Colorado's Leeds School of Business, wanted to explore. Fernbach and his colleagues wondered if forcing people to explain complex policies in detail—not cheerleading for a position but really considering the mechanics of implementation— might force them to confront their ignorance and thus weaken their extremist stands on issues. They ran a series of lab experiments to test this idea

    Question: {{question}} 
    
    Respond below:
    
    ```{{response}}```
    """

@P.semantic_function(formatter=P.allowing_newline)
def Passage3(question:P.Input, response: P.Output):
    """Role: You are a high school student answering questions for an english class. Read the passage below and answer the subsequent question.

    Passage: 
    It is well known that some animal species use camouflage to hide from predators. Individuals that are able to blend in to their surroundings and avoid being eaten are able to survive longer, reproduce, and thus increase their fitness (pass along their genes to the next generation) compared to those who stand out more. This may seem like a good strategy, and fairly common in the animal kingdom, but who ever heard of a plant doing the same thing? In plants, the use of coloration or pigmentation as a vital component of acquiring food (e.g., photosynthesis) or as a means of attracting pollinators (e.g., flowers) has been well studied. However, variation in pigmentation as a means of escaping predation has received little attention. Matthew Klooster from Harvard University and colleagues empirically investigated whether the dried bracts (specialized leaves) on a rare woodland plant, Monotropsis odorata, might serve a similar purpose as the stripes on a tiger or the grey coloration of the wings of the peppered moth: namely, to hide. “Monotropsis odorata is a fascinating plant species, as it relies exclusively upon mycorrhizal fungus, that associates with its roots, for all of the resources it needs to live,” notes Klooster. “Because this plant no longer requires photosynthetic pigmentation (i.e., green coloration) to produce its own energy, it is free to adopt a broader range of possibilities in coloration, much like fungi or animals.” Using a large population of Monotropsis odorata, Klooster and colleagues experimentally removed the dried bracts that cover the 3- to 5-cm tall stems and flower buds of these woodland plants. The bracts are a brown color that resembles the leaf litter from which the reproductive stems emerge and cover the pinkish-purple colored buds and deep purple stems. When Klooster and colleagues measured the reflectance pattern (the percentage of light reflected at various wavelengths) of the different plant parts, they indeed found that the bracts functioned as camouflage, making the plant blend in with its surroundings; the bract reflectance pattern closely resembled that of the leaf litter, and both differed from that of the reproductive stem and flowers hidden underneath the bracts. Furthermore, they experimentally demonstrated that this camouflage actually worked to hide the plant from its predators and increased its fitness. Individuals with intact bracts suffered only a quarter of the herbivore damage and produced a higher percentage of mature fruits compared to those whose bracts were removed. “It has long been shown that animals use cryptic coloration (camouflage) as a defense mechanism to visually match a component of their natural environment, which facilitates predator avoidance,” Klooster said. “We have now experimentally demonstrated that plants have evolved a similar strategy to avoid their herbivores.” Drying its bracts early to hide its reproductive parts is a good strategy when the stems are exposed to predators for long periods of time: all the other species in the subfamily Monotropoideae have colorful fleshy bracts and are reproductively active for only a quarter of the length of time. Somewhat paradoxically, however, Monotropsis odorata actually relies on animals for pollination and seed dispersal. How does it accomplish this when it is disguised as dead leaf material and is able to hide so well? The authors hypothesize that the flowers emit highly fragrant odors that serve to attract pollinators and seed dispersal agents; indeed they observed bumble bees finding and pollinating many reproductive stems that were entirely hidden by the leaf litter itself

    Question: {{question}} 
    
    Response format:
    
    ```{{response}}```
    """


@P.semantic_function(formatter=P.allowing_newline)
def Passage4(question:P.Input, response: P.Output):
    """Role: You are a high school student answering questions for an english class. Read the passage below and answer the subsequent question.

    Passage: 
    To make a government requires no great prudence. Settle the seat of power, teach obedience, and the work is done. To give freedom is still more easy. It is not necessary to guide; it only requires to let go the rein. But to form a free government, that is, to temper together these opposite elements of liberty and restraint in one consistent work, requires much thought, deep reflection, a sagacious, powerful, and combining mind. This I do not find in those who take the lead in the National Assembly. Perhaps they are not so miserably deficient as they appear. I rather believe it. It would put them below the common level of human understanding. But when the leaders choose to make themselves bidders at an auction of popularity, their talents, in the construction of the state, will be of no service. They will become flatterers instead of legislators, the instruments, not the guides, of the people. If any of them should happen to propose a scheme of liberty, soberly limited and defined with proper qualifications, he will be immediately outbid by his competitors who will produce something more splendidly popular. Suspicions will be raised of his fidelity to his cause. Moderation will be stigmatized as the virtue of cowards, and compromise as the prudence of traitors, until, in hopes of preserving the credit which may enable him to temper and moderate, on some occasions, the popular leader is obliged to become active in propagating doctrines and establishing powers that will afterwards defeat any sober purpose at which he ultimately might have aimed. But am I so unreasonable as to see nothing at all that deserves commendation in the indefatigable labors of this Assembly? I do not deny that, among an infinite number of acts of violence and folly, some good may have been done. They who destroy everything certainly will remove some grievance. They who make everything new have a chance that they may establish something beneficial. To give them credit for what they have done in virtue of the authority they have usurped, or which can excuse them in the crimes by which that authority has been acquired, it must appear that the same things could not have been accomplished without producing such a revolution. Most assuredly they might.... Some usages have been abolished on just grounds, but they were such that if they had stood as they were to all eternity, they would little detract from the happiness and prosperity of any state. The improvements of the National Assembly are superficial, their errors fundamental. Whatever they are, I wish my countrymen rather to recommend to our neighbors the example of the British constitution than to take models from them for the improvement of our own. In the former, they have got an invaluable treasure. They are not, I think, without some causes of apprehension and complaint, but these they do not owe to their constitution but to their own conduct. I think our happy situation owing to our constitution, but owing to the whole of it, and not to any part singly, owing in a great measure to what we have left standing in our several reviews and reformations as well as to what we have altered or superadded. Our people will find employment enough for a truly patriotic, free, and independent spirit in guarding what they possess from violation. I would not exclude alteration neither, but even when I changed, it should be to preserve. I should be led to my remedy by a great grievance. In what I did, I should follow the example of our ancestors. I would make the reparation as nearly as possible in the style of the building. A politic caution, a guarded circumspection, a moral rather than a complexional timidity were among the ruling principles of our forefathers in their most decided conduct. Not being illuminated with the light of which the gentlemen of France tell us they have got so abundant a share, they acted under a strong impression of the ignorance and fallibility of mankind. He that had made them thus fallible rewarded them for having in their conduct attended to their nature. Let us imitate their caution if we wish to deserve their fortune or to retain their bequests. Let us add, if we please, but let us preserve what they have left; and, standing on the firm ground of the British constitution, let us be satisfied to admire rather than attempt to follow in their desperate flights the aeronauts of France.

    Question: {{question}} 
    
    Response format:
    
    ```{{response}}```
    """



def main():
    NUM_SAMPLES = 10000
    prefix_choices = [Passage1, Passage2, Passage3, Passage4]
    question_bank = []
    with open('question_bank.txt', r) as f:
        for line in file:
            question_bank.append(line.strip())
    for _ in range(NUM_SAMPLES):
        prefix = random.coice(prefix_choices)
        question = random.choice(question_bank)
        prefix(question)

vm.run(main, timeit=False)
