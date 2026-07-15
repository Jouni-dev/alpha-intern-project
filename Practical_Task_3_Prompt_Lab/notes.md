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




# Challenge 2 — Temperature

-Prompt answer with temperature=0 (First Run):
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Brewed Awakening'? This name plays on the idea of coffee waking you up and the experience of discovering new flavors and blends."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Caffeine Haven'? This name suggests a cozy and welcoming place where coffee lovers can find their perfect brew and enjoy a relaxing atmosphere."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Java Junction'? This name conveys a sense of connection and community, suggesting a place where people come together to enjoy their favorite coffee."}
    
    The answers were different creative coffee shop names, but all followed a similar structure and reasoning pattern.

-Prompt answer with temperature=0 (Second Run):
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Brewed Awakening'? This name plays on the idea of coffee waking you up and the experience of discovering new flavors and blends."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Caffeine Haven'? This name suggests a cozy and welcoming place where coffee lovers can find their perfect brew and enjoy a relaxing atmosphere."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Java Junction'? This name conveys a sense of connection and community, suggesting a place where people come together to enjoy their favorite coffee."}
    
    The answers were IDENTICAL to the first run. Same names in the same order. This proves the model is deterministic at temperature=0.

-Prompt answer with temperature=1.5 (First Run):
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Brew Haven'? It suggests a cozy place where people can enjoy their favorite coffee in a welcoming atmosphere."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Java Junction'? It evokes the idea of a lively meeting place for coffee lovers to gather and enjoy specialty brews."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Bean Scene'? It implies a trendy spot where people come for great coffee and a good atmosphere."}
    
    The answers were noticeably different from each other and from temperature=0 results.

-Prompt answer with temperature=1.5 (Second Run):
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Brewed Awakening'? This name suggests fresh starts and the energizing effects of coffee, while also playing on words to imply that visitors will enjoy a thrilling or enlightening experience."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'Java Junction'? This name conveys a meeting point for coffee lovers and hints at vibrant energy and connection, making it an inviting place to enjoy a cup of coffee."}
    
    You: Invent a name for a coffee shop
    
    Assistant: {'reply': "How about 'The Daily Grind'? This name highlights the daily ritual many have of drinking coffee while also suggesting a casual, welcoming atmosphere where people can relax or be productive."}
    
    The second run produced completely different answers. Even 'Java Junction' appeared twice but with different explanations. This proves temperature=1.5 is random and non-deterministic.

What is the name of the setting you changed, and what is its full range of values?
    The setting is temperature. The full range of values is 0 to 2, with 0 being completely deterministic (identical answers) and 2 being maximally random (highly varied answers).

What value made the answers identical every time? What value made them varied?
    temperature=0 made the answers identical every time. When I ran the same question three times, I got the exact same responses in the exact same order, both on the first run and the second run. 
    
    temperature=1.5 made the answers varied and unpredictable. The first run gave 'Brew Haven', 'Java Junction', and 'Bean Scene'. The second run gave 'Brewed Awakening', 'Java Junction', and 'The Daily Grind'. Even when the same name appeared ('Java Junction'), the explanations were different. This proves temperature=1.5 introduces randomness into the model's output.

Give one real-world example where you'd want the 'identical' setting, and one where you'd want the 'varied' setting.
    Identical (temperature=0): A customer support chatbot should give the same answer to the same question every time. If a customer asks "What is your return policy?" on Monday and again on Friday, they deserve the exact same answer both times for consistency and reliability.
    
    Varied (temperature=1.5): A creative writing assistant should produce different story ideas each time. If a user asks "Give me a creative plot for a sci-fi story," they want variety and surprise, not the same plot repeated every time they ask. High temperature allows the AI to explore different creative directions.


# Challenge 3 — Max Tokens

-Prompt answer with max_tokens=50 (Part A - Forced Truncation):
    You: Explain machine learning in details
    
    [temperature=0.7] [finish_reason=length]
    Assistant: {
      "reply": "Let me think about this: Machine learning (ML) is a subset of artificial intelligence (AI) that enables systems to learn from data, identify patterns, and make decisions with minimal human intervention. It's based on the idea
    
    The answer was cut off mid-sentence. The model ran out of tokens before it could finish explaining machine learning. finish_reason=length proves the model was forced to stop due to the token limit.

-Prompt answer with max_tokens=1024 (Part B - Natural Completion):
    You: Explain machine learning in details
    
    [temperature=0.7] [finish_reason=stop]
    Assistant: Let me think about this: Machine learning (ML) is a subset of artificial intelligence (AI) that focuses on enabling machines to learn from data and improve their performance over time without being explicitly programmed. Let's break this down step-by-step.

    1. **What is Machine Learning?**
       - It's a technique that allows computers to analyze data, identify patterns, and make decisions based on those patterns. Instead of following strict rules coded by humans, ML algorithms learn from examples.

    2. **Types of Machine Learning:** 
       - **Supervised Learning:** In this type, the model is trained on a labeled dataset, meaning the input data has corresponding output labels. For example, if we're teaching a model to recognize animals, we would provide images of cats and dogs with tags indicating which is which. The algorithm learns to associate the features of the images with the correct labels.
       - **Unsupervised Learning:** Here, the model works with unlabeled data. It tries to find patterns or groupings in the data without any prior information about what the output should be. An example is clustering customers into different segments based on their purchasing behavior.
       - **Reinforcement Learning:** This type involves training a model through a system of rewards and penalties. The model learns to make decisions by trying different actions and receiving feedback based on its performance. This is commonly used in robotics and game playing.

    3. **How does Machine Learning work?**
       - **Data Collection:** The first step is to gather data relevant to the problem at hand. This data forms the foundation of the learning process.
       - **Data Preprocessing:** Next, the data is cleaned and transformed into a format suitable for analysis. This may involve removing duplicates, handling missing values, and normalizing data.
       - **Model Selection:** Different algorithms can be used for ML, such as decision trees, neural networks, or support vector machines. The choice of model depends on the problem type and data characteristics.
       - **Training the Model:** The selected model is trained using the prepared dataset. During training, the algorithm adjusts its parameters to minimize errors and improve predictions.
       - **Evaluation:** After training, the model is tested with a separate set of data to evaluate its performance. Metrics such as accuracy, precision, recall, and F1 score are commonly used to assess how well the model performs.
       - **Deployment:** Once validated, the model can be deployed in real-world applications where it can make predictions or decisions based on new data.

    4. **Applications of Machine Learning:**
       - ML is used in various fields, including healthcare (for predicting diseases), finance (for fraud detection), marketing (for customer segmentation), and autonomous vehicles (for navigation and decision making).

    In summary, machine learning involves teaching computers to learn from data and make predictions or decisions. It helps to automate processes and gain insights from large datasets that would be difficult to analyze manually.
    If you have any more questions, I am more than happy to answer them.
    
    The answer completed fully with detailed explanations. finish_reason=stop proves the model finished naturally without hitting the token limit.

Which setting did you use to cut the reply short? Roughly what is one 'token' equal to in plain English?
    I used max_tokens=50 to cut the reply short. One token is roughly equal to 4 characters in plain English, or about 0.75 words. So 50 tokens would be approximately 200 characters or roughly 37-40 words. This is why the response got cut off so quickly when I set max_tokens=50.

What field in the response tells you why the model stopped, and what two different values did you see in it?
    The field is finish_reason in the API response. finish_reason=length means the model ran out of max_tokens and was forced to stop mid-sentence. finish_reason=stop means the model naturally completed its response without hitting the token limit. In Part A, I saw finish_reason=length (truncated). In Part B, I saw finish_reason=stop (natural completion).

Why is capping this setting useful in a real app (think about cost and speed)?
    Capping max_tokens is useful for two main reasons: Cost - OpenAI charges per token used. By setting a lower max_tokens limit, you can reduce the number of tokens generated and therefore reduce your API costs. Speed - Generating fewer tokens means the API responds faster. If you only need a short summary or quick answer, you can cap max_tokens to get a faster response. However, you must balance this carefully - setting it too low (like 50 tokens) results in incomplete answers. In production, you'd set max_tokens based on what your use case requires: low for quick summaries, high for detailed explanations.


