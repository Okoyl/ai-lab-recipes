import os
from llama_cpp import Llama

class Chat:

    def __init__(self, n_ctx=2048) -> None:
        self.chat_history = [
                {"role": "system", "content": """You are a helpful assistant that is comfortable speaking
                with C level executives in a professional setting."""},
                ]
        self.llm = Llama(model_path=os.getenv("MODEL_FILE",
                                    "llama-2-7b-chat.Q5_K_S.gguf"),
                         n_ctx=n_ctx,
                         n_gpu_layers=-1,
                         n_batch=n_ctx,
                         f16_kv=True,
                         stream=True,)
        self.n_ctx = n_ctx


    def reset_system_prompt(self, prompt=None):
        if not prompt:
            self.chat_history[0] = {"role":"system", "content":""}
        else:
            self.chat_history[0] = {"role":"system",
                                  "content": prompt}
        print(self.chat_history[0])


    def clear_history(self):
        self.chat_history = [self.chat_history[0]]


    def count_tokens(self, messages):
        num_extra_tokens = len(self.chat_history) * 6 # accounts for tokens outside of "content"
        token_count = sum([len(self.llm.tokenize(bytes(x["content"], "utf-8"))) for x 
                           in messages]) + num_extra_tokens
        return token_count
    
    
    def clip_history(self, prompt):
        context_length = self.n_ctx
        prompt_length = len(self.llm.tokenize(bytes(prompt["content"], "utf-8")))
        history_length = self.count_tokens(self.chat_history)
        input_length = prompt_length + history_length
        print(input_length)
        while input_length > context_length:
            print("Clipping")
            self.chat_history.pop(1)
            self.chat_history.pop(1)
            history_length = self.count_tokens(self.chat_history)      
            input_length = history_length + prompt_length   
            print(input_length)
    

    def ask(self, prompt, history):
        prompt = {"role":"user", "content":prompt}
        self.chat_history.append(prompt)
        self.clip_history(prompt)
        chat_response = self.llm.create_chat_completion(self.chat_history, stream=True)
        reply = ""
        for i in chat_response:
            token =  i["choices"][0]["delta"] 
            if "content" in token.keys():
                reply += token["content"]
                yield reply
        self.chat_history.append({"role":"assistant","content":reply})

    def summarize(self, prompt, history):
        self.reset_system_prompt("""You are a summarizing agent. 
                                You only respond in bullet points.
                                Your only job is to summarize your inputs and provide the most concise possible output. 
                                Do not add any information that does not come directly from the user prompt.
                                Limit your response to a maximum of 5 bullet points.
                                 It's fine to have less than 5 bullet points"""
                                )
        
        prompt = {"role":"user","content": prompt}
        self.chat_history.append(prompt)
        chat_response = self.llm.create_chat_completion(self.chat_history)
        self.clear_history()
        return chat_response["choices"][0]["message"]["content"]
        
