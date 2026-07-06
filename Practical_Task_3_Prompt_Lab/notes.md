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


