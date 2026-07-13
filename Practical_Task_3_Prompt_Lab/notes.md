# Prompt Lab — Findings
 
# Challenge 1 — System vs User Messages 
-Prompt answer without any personality:
    You: What is the capital of France?

    Assistant: {'reply': 'The capital of France is Paris.'}
    As we can see the answer is normal without any villan personality mixed into the answer

-Prompt answer after the villanous personality was added to the system message:
    You: What is the capital of France?

    Assistant: 
    {'reply': 'Ah, you dare to inquire about the beating heart of France, the city of lights! It is none other than Paris, that elegant jewel of the Seine, where romance intertwines with the shadows of history! Cackles echo through the ages! Paris, the capital that has witnessed revolutions and romances alike, a city that beckons to the souls of dreamers and schemers! But beware, for knowledge is a double-edged sword, my naive interlocutor! What other secrets do you wish to uncover, or shall you cower in ignorance?'}

    The answer contained the villanous personality very obviously.

-Prompt answer with the villanous personality added to the user message 
    You:  What is the capital of France?    

    Assistant: 
    Ah, you dare to question the depths of my vast, nefarious knowledge? How quaint! The answer you seek, oh unsuspecting mortal, is none other than PARIS! Yes, the City of Lights, where romance and treachery entwine in a dance as old as time itself! 

    But do not be fooled by its beauty, for beneath its enchanting facade lies a labyrinth of shadows and secrets! My evil plan, you ask? To plunge this majestic city into eternal darkness, where the Eiffel Tower shall be my ominous beacon of dread! 

    Cackle, cackle, cackle! Yes, laugh at your own ignorance, for you have merely scratched the surface of my diabolical intellect! Paris! The heart of France! But soon, my dear, it shall be the heart of chaos! Mwahahaha!

What is the difference between the system message and the user message? Which one sets behaviour, which one carries the request?
    For the system message it answered every question consistently as a villon would.
    For the user message it carried a specific given request for this turn only.

What happened when you put the villain instruction in the user message instead of the system message? Why?
    The system treated it as a request for a only the period of this question for while in the system it used it as its whole personality so every request we gave it, it followed the villanous personality.
    
In your own words: when should an instruction go in the system message vs the user message?
    It should go in the system message when we are interested in making our ai with a certain personaility for all chats throughout all the tasks. The prompt should be added to the user message when we want it to take the personality for only this run/task.



