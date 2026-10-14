"""Flet presentation layer for the offline-first SugarBalance SA app."""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Callable

import flet as ft

from database import (
    add_health_log,
    delete_health_log,
    get_recent_logs,
    initialize_database,
)
from herbs import search_herbs
from localization import SUPPORTED_LANGUAGES, load_translations
from recipes import search_recipes


_DEFAULT_VALIDATION_MESSAGES = {
    "error_whole_number": "{field} must be a whole number.",
    "error_positive_number": "{field} must be a positive number.",
    "error_glucose_number": "Glucose must be a valid number.",
    "error_glucose_positive": "Glucose must be a positive, finite number.",
    "error_both_pressure": "Enter both systolic and diastolic blood pressure values.",
    "error_required_reading": "Enter blood pressure or glucose before saving.",
}


def _message(key: str, translate: Callable[[str], str] | None) -> str:
    if translate is not None:
        return translate(key)
    return _DEFAULT_VALIDATION_MESSAGES[key]


def _parse_optional_int(
    value: str | None,
    field_name: str,
    translate: Callable[[str], str] | None = None,
) -> int | None:
    """Parse a blankable positive integer field."""
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = int(text)
    except ValueError as exc:
        message = _message("error_whole_number", translate).format(field=field_name)
        raise ValueError(message) from exc
    if parsed <= 0:
        message = _message("error_positive_number", translate).format(field=field_name)
        raise ValueError(message)
    return parsed


def _parse_optional_glucose(
    value: str | None,
    translate: Callable[[str], str] | None = None,
) -> float | None:
    """Parse a blankable positive finite glucose value."""
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError as exc:
        raise ValueError(_message("error_glucose_number", translate)) from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(_message("error_glucose_positive", translate))
    return parsed


def _parse_health_readings(
    systolic: str | None,
    diastolic: str | None,
    glucose: str | None,
    translate: Callable[[str], str] | None = None,
) -> tuple[int | None, int | None, float | None]:
    """Parse readings and ensure a blood-pressure pair or glucose is provided."""
    systolic_value = _parse_optional_int(
        systolic,
        translate("systolic_name") if translate else "Systolic pressure",
        translate,
    )
    diastolic_value = _parse_optional_int(
        diastolic,
        translate("diastolic_name") if translate else "Diastolic pressure",
        translate,
    )
    glucose_value = _parse_optional_glucose(glucose, translate)
    if (systolic_value is None) != (diastolic_value is None):
        raise ValueError(_message("error_both_pressure", translate))
    if systolic_value is None and glucose_value is None:
        raise ValueError(_message("error_required_reading", translate))
    return systolic_value, diastolic_value, glucose_value


def main(page: ft.Page) -> None:
    page.title = "SugarBalance SA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.TEAL_700,
        use_material3=True,
    )
    page.bgcolor = "#F3F8F7"
    page.padding = 0
    page.window_min_width = 360
    page.window_min_height = 600
    initialize_database()
    translations = load_translations("en")

    def tr(key: str) -> str:
        return translations[key]

    def notify(message: str, error: bool = False) -> None:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
        )
        page.snack_bar.open = True
        page.update()

    systolic = ft.TextField(
        label=tr("systolic_label"),
        hint_text=tr("systolic_hint"),
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True,
    )
    diastolic = ft.TextField(
        label=tr("diastolic_label"),
        hint_text=tr("diastolic_hint"),
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True,
    )
    glucose = ft.TextField(
        label=tr("glucose_label"),
        hint_text=tr("glucose_hint"),
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    notes = ft.TextField(
        label=tr("notes_label"),
        multiline=True,
        min_lines=1,
        max_lines=3,
    )
    log_list = ft.Column(spacing=8)

    def refresh_logs() -> None:
        log_list.controls.clear()
        logs = get_recent_logs()
        if not logs:
            log_list.controls.append(ft.Text(tr("no_logs")))
        for entry in logs:
            recorded = entry["recorded_at"].replace("T", " ")
            readings = []
            if entry["systolic"] is not None or entry["diastolic"] is not None:
                readings.append(
                    tr("blood_pressure_value").format(
                        systolic=entry["systolic"] if entry["systolic"] is not None else "—",
                        diastolic=entry["diastolic"] if entry["diastolic"] is not None else "—",
                    )
                )
            if entry["glucose"] is not None:
                readings.append(
                    tr("glucose_value").format(value=f'{entry["glucose"]:g}')
                )
            description = " · ".join(readings) + f"\n{recorded}"
            if entry["notes"]:
                description += f'\n{entry["notes"]}'
            log_list.controls.append(
                ft.Card(
                    elevation=1,
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(description, expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip=tr("delete_reading"),
                                    data=entry["id"],
                                    on_click=lambda event: remove_log(event.control.data),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=10,
                    )
                )
            )

    def remove_log(log_id: int) -> None:
        try:
            delete_health_log(log_id)
            refresh_logs()
            page.update()
            notify(tr("health_deleted"))
        except sqlite3.Error as exc:
            notify(tr("error_delete").format(error=exc), error=True)

    def save_log(_: ft.ControlEvent) -> None:
        try:
            systolic_value, diastolic_value, glucose_value = _parse_health_readings(
                systolic.value,
                diastolic.value,
                glucose.value,
                tr,
            )
            add_health_log(
                systolic=systolic_value,
                diastolic=diastolic_value,
                glucose=glucose_value,
                notes=notes.value or "",
            )
            systolic.value = ""
            diastolic.value = ""
            glucose.value = ""
            notes.value = ""
            refresh_logs()
            page.update()
            notify(tr("health_saved"))
        except ValueError as exc:
            notify(str(exc) or tr("error_required_reading"), error=True)
        except sqlite3.Error as exc:
            notify(tr("error_save").format(error=exc), error=True)

    refresh_logs()

    tracker_title = ft.Text(
        tr("tracker_title"),
        size=24,
        weight=ft.FontWeight.BOLD,
    )
    tracker_intro = ft.Text(tr("tracker_intro"))
    add_reading_title = ft.Text(
        tr("add_reading"),
        size=18,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.TEAL_900,
    )
    blood_pressure_title = ft.Text(
        tr("blood_pressure_group"),
        weight=ft.FontWeight.W_600,
    )
    glucose_title = ft.Text(
        tr("glucose_group"),
        weight=ft.FontWeight.W_600,
    )
    save_button = ft.FilledButton(
        tr("save_button"),
        icon=ft.Icons.ADD,
        on_click=save_log,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.TEAL_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )
    recent_readings_title = ft.Text(
        tr("recent_readings"),
        size=19,
        weight=ft.FontWeight.BOLD,
    )

    tracker_tab = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.MONITOR_HEART, color=ft.Colors.TEAL_700, size=28),
                    tracker_title,
                ],
                spacing=10,
            ),
            tracker_intro,
            ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=16,
                    border_radius=16,
                    content=ft.Column(
                        [
                            add_reading_title,
                            blood_pressure_title,
                            ft.Row([systolic, diastolic], wrap=True),
                            glucose_title,
                            glucose,
                            notes,
                            save_button,
                        ],
                        spacing=12,
                    ),
                ),
            ),
            ft.Row(
                [
                    ft.Icon(ft.Icons.HISTORY, color=ft.Colors.TEAL_700),
                    recent_readings_title,
                ],
                spacing=8,
            ),
            log_list,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    recipe_results = ft.Column(spacing=10)
    recipe_search = ft.TextField(
        label=tr("search_recipes"),
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda _: render_recipes(),
    )

    def render_recipes() -> None:
        recipe_results.controls.clear()
        for recipe in search_recipes(recipe_search.value or ""):
            recipe_results.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(recipe.name, size=18, weight=ft.FontWeight.BOLD),
                                ft.Text(recipe.description),
                                ft.Text(
                                    f'{tr("ingredients")}: '
                                    + "; ".join(recipe.ingredients)
                                ),
                                ft.Text(
                                    f'{tr("method")}: '
                                    + " ".join(recipe.steps)
                                ),
                                ft.Text(
                                    f'{tr("tags")}: ' + ", ".join(recipe.tags),
                                    italic=True,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=16,
                        border_radius=16,
                    )
                )
            )
        if not recipe_results.controls:
            recipe_results.controls.append(ft.Text(tr("no_recipes")))
        page.update()

    render_recipes()
    cookbook_title = ft.Text(
        tr("cookbook_title"),
        size=24,
        weight=ft.FontWeight.BOLD,
    )
    cookbook_intro = ft.Text(tr("cookbook_intro"))
    cookbook_tab = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.RESTAURANT, color=ft.Colors.TEAL_700, size=28),
                    cookbook_title,
                ],
                spacing=10,
            ),
            cookbook_intro,
            recipe_search,
            recipe_results,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    herb_results = ft.Column(spacing=10)
    herb_search = ft.TextField(
        label=tr("search_herbs"),
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda _: render_herbs(),
    )

    def render_herbs() -> None:
        herb_results.controls.clear()
        for herb in search_herbs(herb_search.value or ""):
            herb_results.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(herb.name, size=18, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f'{tr("also_known_as")}: '
                                    + ", ".join(herb.local_names)
                                ),
                                ft.Text(
                                    f'{tr("traditional_use")}: '
                                    + herb.traditional_use
                                ),
                                ft.Text(
                                    f'{tr("evidence")}: ' + herb.evidence_note
                                ),
                                ft.Text(
                                    f'{tr("medication_warning")}: '
                                    + herb.medication_warning
                                ),
                                ft.Text(
                                    f'{tr("important")}: '
                                    + " ".join(herb.red_flags),
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=16,
                        border_radius=16,
                    )
                )
            )
        if not herb_results.controls:
            herb_results.controls.append(ft.Text(tr("no_herbs")))
        page.update()

    render_herbs()
    herbs_title = ft.Text(
        tr("herbs_title"),
        size=24,
        weight=ft.FontWeight.BOLD,
    )
    herbal_warning = ft.Text(tr("general_herbal_warning"))
    herbs_tab = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.SPA, color=ft.Colors.TEAL_700, size=28),
                    herbs_title,
                ],
                spacing=10,
            ),
            ft.Container(
                content=herbal_warning,
                padding=12,
                bgcolor=ft.Colors.AMBER_100,
                border_radius=8,
            ),
            herb_search,
            herb_results,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    content_area = ft.Container(
        content=tracker_tab,
        expand=True,
        padding=18,
    )

    views = (tracker_tab, cookbook_tab, herbs_tab)

    def change_view(event: ft.ControlEvent) -> None:
        content_area.content = views[event.control.selected_index]
        page.update()

    navigation = ft.NavigationBar(
        selected_index=0,
        on_change=change_view,
        bgcolor=ft.Colors.WHITE,
        indicator_color="#CCFBF1",
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        animation_duration=300,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.MONITOR_HEART,
                selected_icon=ft.Icons.MONITOR_HEART,
                label=tr("nav_tracker"),
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.RESTAURANT,
                selected_icon=ft.Icons.RESTAURANT,
                label=tr("nav_cookbook"),
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SPA,
                selected_icon=ft.Icons.SPA,
                label=tr("nav_herbs"),
            ),
        ],
    )

    language_code = "en"

    def apply_language(event: ft.ControlEvent) -> None:
        nonlocal language_code, translations
        selected_language = event.control.value
        try:
            updated_translations = load_translations(selected_language)
        except (OSError, ValueError) as exc:
            language_selector.value = language_code
            notify(f"Could not load language catalog: {exc}", error=True)
            return

        translations = updated_translations
        language_code = selected_language
        language_selector.label = tr("language")
        tagline_text.value = tr("tagline")
        offline_text.value = tr("offline")

        systolic.label = tr("systolic_label")
        systolic.hint_text = tr("systolic_hint")
        diastolic.label = tr("diastolic_label")
        diastolic.hint_text = tr("diastolic_hint")
        glucose.label = tr("glucose_label")
        glucose.hint_text = tr("glucose_hint")
        notes.label = tr("notes_label")

        tracker_title.value = tr("tracker_title")
        tracker_intro.value = tr("tracker_intro")
        add_reading_title.value = tr("add_reading")
        blood_pressure_title.value = tr("blood_pressure_group")
        glucose_title.value = tr("glucose_group")
        save_button.text = tr("save_button")
        recent_readings_title.value = tr("recent_readings")
        cookbook_title.value = tr("cookbook_title")
        cookbook_intro.value = tr("cookbook_intro")
        recipe_search.label = tr("search_recipes")
        herbs_title.value = tr("herbs_title")
        herbal_warning.value = tr("general_herbal_warning")
        herb_search.label = tr("search_herbs")

        navigation.destinations[0].label = tr("nav_tracker")
        navigation.destinations[1].label = tr("nav_cookbook")
        navigation.destinations[2].label = tr("nav_herbs")

        refresh_logs()
        render_recipes()
        render_herbs()
        page.update()

    language_selector = ft.Dropdown(
        label=tr("language"),
        value=language_code,
        width=190,
        options=[
            ft.dropdown.Option(code, text=name)
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
        on_select=apply_language,
    )

    def go_to_tracker(_: ft.ControlEvent | None = None) -> None:
        navigation.selected_index = 0
        content_area.content = tracker_tab
        page.update()

    def animate_logo(event: ft.HoverEvent) -> None:
        logo_mark.scale = 1.06 if event.data == "true" else 1.0
        page.update()

    logo_mark = ft.Container(
        content=ft.Icon(
            ft.Icons.MONITOR_HEART,
            size=34,
            color=ft.Colors.WHITE,
        ),
        width=64,
        height=64,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#2DD4BF", "#0F766E"],
        ),
        border_radius=20,
        shadow=ft.BoxShadow(
            blur_radius=18,
            spread_radius=1,
            color="#50000000",
            offset=ft.Offset(0, 6),
        ),
        animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        on_hover=animate_logo,
        on_click=go_to_tracker,
        tooltip=tr("go_tracker"),
    )
    tagline_text = ft.Text(
        tr("tagline"),
        size=10,
        weight=ft.FontWeight.W_600,
        color="#CCFBF1",
    )
    offline_text = ft.Text(
        tr("offline"),
        size=11,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    brand_title = ft.Text(
        "SugarBalance",
        size=25,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )

    page.navigation_bar = navigation
    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    logo_mark,
                                    ft.Column(
                                        [
                                            brand_title,
                                            tagline_text,
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                ],
                                spacing=14,
                            ),
                            ft.Row(
                                [
                                    language_selector,
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.CLOUD_OFF,
                                                    size=15,
                                                    color="#CCFBF1",
                                                ),
                                                offline_text,
                                            ],
                                            spacing=5,
                                        ),
                                        padding=ft.Padding.symmetric(
                                            horizontal=10,
                                            vertical=7,
                                        ),
                                        bgcolor="#33000000",
                                        border_radius=20,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=12,
                        tight=True,
                    ),
                    padding=ft.Padding.only(
                        left=20,
                        right=20,
                        top=18,
                        bottom=18,
                    ),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=["#134E4A", "#0F766E", "#115E59"],
                    ),
                ),
                content_area,
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.run(main)