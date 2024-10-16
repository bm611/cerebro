import reflex as rx


def todo() -> rx.Component:
    return rx.container(
        rx.markdown(
            """
          ## Build out UI with `option` tab for user input
          - Prompt
          - Document
          - Video
          - Image

          ## Display generated quiz
          - Grid layout
          - arrow button to navigate

          ## Backend
          - Implement user authentication
          - Create database schema
          - Set up API endpoints
        """
        ),
    )
