# src/quiz.py
import textwrap
from .cohere_ai import explain_mistake
import pygame
import sys
import random

from .settings import WIDTH, HEIGHT, FPS, BLACK, WHITE, IMG_DIR

def wrap_text(text, font, max_width):
    """
    Splits 'text' into multiple lines so each line does not exceed 'max_width'
    when rendered with 'font'. Returns a list of lines.
    """
    words = text.split()
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        test_surface = font.render(word + " ", True, WHITE)
        word_width = test_surface.get_width()

        if current_width + word_width <= max_width:
            current_line.append(word + " ")
            current_width += word_width
        else:
            lines.append("".join(current_line))
            current_line = [word + " "]
            current_width = word_width

    if current_line:
        lines.append("".join(current_line))

    return lines

def wrap_text_lines(text, font, max_width):
    """Splits text into lines that fit within max_width when rendered with font."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if font.size(test_line)[0] <= max_width - 20:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def wrap_and_scale_text(text, font_path, max_width, max_height, base_size, color):
    """
    Returns a list of (surface, rect) for each line of wrapped text
    that fits within max_width and max_height by scaling font size down as needed.
    """
    size = base_size
    while size >= 10:
        font = pygame.font.Font(font_path, size)
        lines = wrap_text_lines(text, font, max_width)
        line_height = font.get_linesize()
        total_height = len(lines) * line_height

        if total_height <= max_height:
            rendered_lines = []
            for i, line in enumerate(lines):
                surf = font.render(line, True, color)
                rect = surf.get_rect()
                rendered_lines.append((surf, rect))
            return rendered_lines, line_height

        size -= 1  # Try smaller font size

    # Fallback: tiny font
    font = pygame.font.Font(font_path, 10)
    lines = wrap_text_lines(text, font, max_width)
    rendered_lines = [(font.render(line, True, color), font.render(line, True, color).get_rect()) for line in lines]
    return rendered_lines, font.get_linesize()

def show_quiz(surface, clock, font, question):
    """
    Displays a quiz with multiple choice answers on 'surface'.
    Returns the answer string chosen by the user.
    Pauses the main loop until an answer is clicked.
    """
    # Get the question text and build the answers list.
    question_text = question["question"]
    incorrect_answers = question["incorrect"][:3]  # copy incorrect answers
    answers = incorrect_answers + [question["correct"]]       # add the correct answer
    random.shuffle(answers)                   # shuffle all answers

    quiz_width, quiz_height = 800, 600
    quiz_x = (WIDTH - quiz_width) // 2
    quiz_y = (HEIGHT - quiz_height) // 2
    quiz_rect = pygame.Rect(quiz_x, quiz_y, quiz_width, quiz_height)

    # Define a question text box at the top of the quiz window.
    question_box_margin = 20
    question_box_height = 150  # adjust as needed for long questions
    question_box = pygame.Rect(
        quiz_rect.left + question_box_margin,
        quiz_rect.top + question_box_margin,
        quiz_rect.width - 2 * question_box_margin,
        question_box_height
    )

    # Wrap the question text to fit within the question_box.
    lines = wrap_text(question_text, font, question_box.width - 20)
    line_spacing = font.get_linesize()

    # Define answer button grid (2×2 layout) positioned below the question box.
    button_width, button_height = 300, 80
    spacing = 20  # space between buttons
    grid_width = 2 * button_width + spacing
    grid_height = 2 * button_height + spacing

    grid_x = quiz_rect.left + (quiz_width - grid_width) // 2
    grid_y = question_box.bottom + 20  # 20 pixels below the question box

    buttons = []
    for i, ans in enumerate(answers):
        row = i // 2
        col = i % 2
        btn_x = grid_x + col * (button_width + spacing)
        btn_y = grid_y + row * (button_height + spacing)
        rect = pygame.Rect(btn_x, btn_y, button_width, button_height)
        buttons.append((ans, rect))

    # Load and position the assistant icon within the quiz window.
    assistant_icon_size = 150
    assistant_img = pygame.image.load(f"{IMG_DIR}/assistant.png").convert_alpha()
    assistant_img = pygame.transform.scale(assistant_img, (assistant_icon_size, assistant_icon_size))
    assistant_icon_rect = pygame.Rect(
        quiz_rect.left + 10,
        quiz_rect.bottom - assistant_icon_size - 10,
        assistant_icon_size,
        assistant_icon_size
    )

    # Get hint text if available.
    hint_text = question.get("hint", "Need a hint? Click me!")
    hint_chunks = textwrap.wrap(hint_text, 60)
    current_hint_index = 0
    hint_shown = False  # Toggle for showing the hint bubble

    explanation_mode = False
    explanation_chunks = []
    explanation_index = 0
    selected_answer = None

    quiz_running = True

    while quiz_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if explanation_mode:
                    hint_shown = True
                    explanation_index += 1
                    if explanation_index >= len(explanation_chunks):
                        # End explanation mode and return the wrong answer.
                        return selected_answer
                    continue
                if assistant_icon_rect.collidepoint(mouse_pos):
                    hint_shown = True
                    current_hint_index = (current_hint_index + 1) % len(
                        hint_chunks)

                for ans, rect in buttons:
                    if rect.collidepoint(mouse_pos):
                        if ans != question["correct"]:
                            question_explanation = explain_mistake(
                                question_text, [question["correct"]], ans)
                            print(question_explanation)
                            explanation_chunks = textwrap.wrap(
                                question_explanation, 60)
                            explanation_index = 0
                            explanation_mode = True
                        else:
                            return ans

        # Dim the background.
        surface.fill(BLACK)
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(120)
        overlay.fill((50, 50, 50))
        surface.blit(overlay, (0, 0))

        # Draw the quiz window.
        pygame.draw.rect(surface, BLACK, quiz_rect)
        pygame.draw.rect(surface, WHITE, quiz_rect, 2)

        # Draw the question box.
        pygame.draw.rect(surface, BLACK, question_box)
        pygame.draw.rect(surface, WHITE, question_box, 2)

        # Render the wrapped question text within the question box.
        text_y = question_box.top + 10
        for line in lines:
            line_surf = font.render(line, True, WHITE)
            line_rect = line_surf.get_rect(x=question_box.left + 10, y=text_y)
            surface.blit(line_surf, line_rect)
            text_y += line_spacing

        # Draw the assistant icon.
        surface.blit(assistant_img, assistant_icon_rect)
        if hint_shown and not explanation_mode:
            hint_font = pygame.font.Font("assets/PixelifySans.ttf", 20)
            # Get the current hint chunk.
            current_hint = hint_chunks[current_hint_index - 1]
            hint_surf = hint_font.render(current_hint, True, WHITE)
            hint_rect = hint_surf.get_rect()
            hint_rect.bottomleft = (
                assistant_icon_rect.left - 10, assistant_icon_rect.top - 25)
            bubble_rect = hint_rect.inflate(20, 20)
            pygame.draw.rect(surface, (50, 50, 50), bubble_rect,
                             border_radius=8)
            pygame.draw.rect(surface, WHITE, bubble_rect, 2, border_radius=8)
            surface.blit(hint_surf, hint_rect)

        # Draw answer buttons
        if not explanation_mode:
            for ans, rect in buttons:
                pygame.draw.rect(surface, (100, 100, 100), rect)
                pygame.draw.rect(surface, WHITE, rect, 2)

                # Wrap and scale text to fit within the button
                text_surfaces, line_height = wrap_and_scale_text(
                    ans,
                    "assets/font.ttf",  # your font file
                    rect.width - 20,
                    rect.height - 20,
                    28,  # starting font size
                    WHITE
                )

                # Calculate top Y to center vertically
                total_text_height = len(text_surfaces) * line_height
                start_y = rect.top + (rect.height - total_text_height) // 2

                for i, (surf, _) in enumerate(text_surfaces):
                    rect_line = surf.get_rect(centerx=rect.centerx, y=start_y + i * line_height)
                    surface.blit(surf, rect_line)

        if explanation_mode:
            box_width, box_height = 600, 200
            box_x = (WIDTH - box_width) // 2
            box_y = (HEIGHT - box_height) // 2
            explanation_box = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(surface, WHITE, explanation_box, 2)
            # Display the current explanation chunk.
            if explanation_index < len(explanation_chunks):
                chunk_text = explanation_chunks[explanation_index]
            else:
                chunk_text = ""
            text_surface = font.render(chunk_text, True, WHITE)
            text_rect = text_surface.get_rect(center=explanation_box.center)
            surface.blit(text_surface, text_rect)
            # Display a "Click to continue" message below the box.
            continue_msg = font.render("Click to continue", True, WHITE)
            continue_rect = continue_msg.get_rect(
                center=(WIDTH // 2, box_y + box_height + 20))
            surface.blit(continue_msg, continue_rect)

        scaled_surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))
        pygame.display.get_surface().blit(scaled_surface, (0, 0))
        pygame.display.flip()
