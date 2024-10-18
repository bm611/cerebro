import reflex as rx
from pages import todo
from dotenv import load_dotenv
import google.generativeai as genai
import os
from typing import List, Dict, Any
import json

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# gemini api config
genai.configure(api_key=GEMINI_API_KEY)
model_json = genai.GenerativeModel(
    "gemini-1.5-flash-002",
    generation_config={"response_mime_type": "application/json"},
)
# model = genai.GenerativeModel("gemini-1.5-flash")


def generate_quiz_json(user_question: str):
    SEARCH_PROMPT = f"""
    You are an expert at generating quiz based on a user prompt.
    Generate 10 single choice quiz question about the topic provide below. the json should have question, choices and answer.

    json schema example:
      {{
         "quiz":[
            {{
              "quiz_title" : "<generate title here..>",
               "difficulty":"easy",
               "question":"What is the basic unit of a neural network?",
               "choices":[
                  "Synapse",
                  "Neuron",
                  "Axon",
                  "Dendrite"
               ],
               "answer":"Neuron"
            }}
         ]
      }}

    USER QUESTION: {user_question}
    """
    response = model_json.generate_content(SEARCH_PROMPT).text
    response = json.loads(response)["quiz"]
    return response


class SegmentedState(rx.State):
    control: str = "prompt"


class State(rx.State):
    query: str = ""
    response: List[Dict[str, Any]] = [{"question": "", "choices": []}]
    current_question_index: int = 0
    is_generating: bool = False
    selected_option: str = ""
    # is_correct: bool = False
    show_answer: bool = False

    # for handling radio button option
    def handle_selection(self, value: str):
        self.show_answer = False
        self.selected_option = value

    def set_query(self, query: str):
        self.query = query

    def start_generation(self):
        self.is_generating = True

    def handle_submit(self):
        self.response = generate_quiz_json(self.query)
        self.query = ""
        self.is_generating = False
        return rx.redirect("/quiz")

    def next_question(self):
        if self.display_index < len(self.response):
            self.current_question_index += 1
        self.show_answer = False

    def previous_question(self):
        if self.display_index > 1:
            self.current_question_index -= 1

    def check_answer(self):
        self.show_answer = True
        # if State.selected_option == State.current_question["answer"]:
        #     self.is_correct = True

    @rx.var
    def display_index(self) -> int:
        return self.current_question_index + 1

    @rx.var
    def current_question(self) -> Dict[str, Any]:
        return self.response[self.current_question_index]

    @rx.var
    def current_choices(self) -> List[str]:
        return self.current_question["choices"]


@rx.page(route="/", title="home")
def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading(
                "Cerebro",
                class_name="text-6xl font-normal text-black",
            ),
            rx.spacer(),
            rx.heading(
                "Generate quiz based on prompt or by uploading a document",
                class_name="mt-10 text-3xl font-normal text-center text-black",
            ),
            rx.text(
                "Generate quizzes effortlessly with AI-powered tool. Simply upload a document or provide a prompt, and get a tailored quiz to reinforce learning and assess understanding.",
                class_name="md:px-0 px-2 mt-4 text-lg text-gray-500 text-center max-w-2xl mx-auto",
            ),
            rx.vstack(
                rx.segmented_control.root(
                    rx.segmented_control.item("By File", value="file"),
                    rx.segmented_control.item("By Prompt", value="prompt"),
                    on_change=SegmentedState.setvar("control"),
                    value=SegmentedState.control,
                ),
                rx.cond(
                    SegmentedState.control == "file",
                    rx.upload(
                        rx.text(
                            "Drag and drop files here or click to select files",
                            class_name="text-center",
                        ),
                        class_name="w-full md:w-3/4 h-40 p-2 border border-blue-600 rounded-2xl mt-4",
                    ),
                    rx.vstack(
                        rx.text_area(
                            placeholder="Enter your prompt here...",
                            value=State.query,
                            on_change=State.set_query,
                            class_name="bg-transparent w-full md:w-3/4 h-40 p-2 border border-blue-600 rounded-2xl mt-4 text-black",
                        ),
                        rx.button(
                            "Generate Quiz",
                            on_click=[
                                State.start_generation,
                                State.handle_submit,
                            ],
                            class_name="mt-4 px-4 py-2 bg-gray-600 hover:bg-gray-800 text-white rounded-md",
                            loading=State.is_generating,
                            disabled=State.is_generating,
                        ),
                        class_name="w-full flex items-center",
                    ),
                ),
                class_name="w-full mt-10 flex items-center justify-center",
            ),
            class_name="mt-10 flex items-center justify-center",
        ),
    )


@rx.page(route="tracker", title="tracker")
def render_todo() -> rx.Component:
    return todo.todo()


@rx.page(route="quiz", title="quiz")
def render_quiz() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading(
                "Cerebro",
                class_name="mb-20 text-6xl text-black font-normal hover:cursor-pointer",
                on_click=rx.redirect("/"),
            ),
            rx.hstack(
                rx.match(
                    State.current_question["difficulty"],
                    (
                        "easy",
                        rx.badge(
                            "easy",
                            color_scheme="grass",
                            variant="outline",
                            high_contrast=False,
                        ),
                    ),
                    (
                        "medium",
                        rx.badge(
                            "medium",
                            color_scheme="yellow",
                            variant="outline",
                            high_contrast=False,
                        ),
                    ),
                    (
                        "hard",
                        rx.badge(
                            "hard",
                            color_scheme="tomato",
                            variant="outline",
                            high_contrast=False,
                        ),
                    ),
                ),
                rx.text(State.current_question["quiz_title"]),
                rx.text(f"{State.display_index}/{State.response.length().to_string()}"),
                class_name="md:w-3/4 justify-between items-center px-2 w-full md:md:px-4",
            ),
            rx.box(
                rx.vstack(
                    rx.text("Question", class_name="text-sm"),
                    rx.card(
                        rx.text(State.current_question["question"]),
                        class_name="w-full text-sm bg-gray-400",
                    ),
                    rx.radio(
                        State.current_choices,
                        value=State.selected_option,
                        on_change=State.handle_selection,
                        direction="column",
                        spacing="2",
                        size="2",
                    ),
                    class_name="p-4",
                ),
                class_name="border-2 border-black w-full md:w-3/4 rounded-3xl",
            ),
            rx.cond(
                State.show_answer,
                rx.cond(
                    State.selected_option == State.current_question["answer"],
                    rx.badge(
                        rx.icon("circle-check", size=18),
                        "Correct",
                        color_scheme="grass",
                        variant="solid",
                        high_contrast=False,
                        radius="full",
                        size="3",
                    ),
                    rx.badge(
                        rx.icon("circle-x", size=18),
                        "Wrong",
                        color_scheme="tomato",
                        variant="solid",
                        high_contrast=False,
                        radius="full",
                        size="3",
                    ),
                ),
                rx.text(""),
            ),
            rx.button(
                "Check Answer",
                on_click=State.check_answer,
                class_name="mt-4 px-4 py-2 bg-gray-600 hover:bg-gray-800 text-white rounded-md",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("chevron-left", color="black"),
                    variant="outline",
                    on_click=State.previous_question,
                ),
                rx.spacer(),
                rx.spacer(),
                rx.button(
                    rx.icon("chevron-right", color="black"),
                    variant="outline",
                    on_click=State.next_question,
                ),
                class_name="mt-6",
            ),
            class_name="w-full mt-10 flex items-center justify-center",
        ),
    )


style = {
    "font_family": "Lexend",
    "font_size": "16px",
    "background": "linear-gradient(to bottom, #f0f0f0, #ffffff)",
}

app = rx.App(
    style=style,
    stylesheets=[
        "/fonts/font.css",  # This path is relative to assets/
    ],
    theme=rx.theme(
        appearance="light",
        has_background=True,
    ),
)
