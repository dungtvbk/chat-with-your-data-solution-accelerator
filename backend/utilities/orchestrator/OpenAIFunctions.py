from typing import List

from backend.utilities.tools.QuestionAnswerTool import QuestionAnswerTool
from .OrchestratorBase import OrchestratorBase
from ..LLMHelper import LLMHelper
from ..parser.OutputParserTool import OutputParserTool
from ..tools.Answer import Answer
import json

class OpenAIFunctionsOrchestrator(OrchestratorBase):
    def __init__(self) -> None:
        super().__init__()     

        self.functions = [
            {
                "name": "search_documents",
                "description": "Provide answers to any fact question coming from users.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "A standalone question, converted from the chat history",
                        },
                    },
                    "required": ["question"],
                },
            },
        ]
        
    def orchestrate(self, user_message: str, chat_history: List[dict], **kwargs: dict) -> dict:
        
        # Call Content Safety tool
        
        
        # Call function to determine route
        llm_helper = LLMHelper()
        system_message = """You are an AI assistant that helps users answers questions using private information sources. You must prioritize the function call over your general knowledge for any fact-based question by calling the search_documents function. When you do this, you take the user's question and convert it into a standalone question, given the chat history listed below. If the user asks multiple questions at once, break them up into multiple standalone questions, all in one line. If the user asks you to perform operations on prior messages, you just help them to do that.

        Chat History:
        {chat_history}

        You are permitted to perform normal chit chat.
        """

        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
        result = llm_helper.get_chat_completion(messages, self.functions, function_call="auto")
        print("function: ", result['choices'][0])
        
        # TODO: call content safety if needed
        
        # if question
        if result['choices'][0]['finish_reason'] == "function_call":
            
            question = json.loads(result['choices'][0]['message']['function_call']['arguments'])['question']          
            # run answering chain
            answering_tool = QuestionAnswerTool()
            answer = answering_tool.answer_question(question, chat_history)
            # TODO: run post prompt if needed
            
        else:
            text = result['choices'][0]['message']['content']
            answer = Answer(question=user_message, answer=text)
        # TODO: call content safety if needed
        
        output_formatter = OutputParserTool()
        messages = output_formatter.parse(question=answer.question, answer=answer.answer, source_documents=answer.source_documents)
        
        return messages
        
        

    