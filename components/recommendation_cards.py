"""Cartes « Priorité » de la page Recommandations : en-tête (icône, titre, badge, ⓘ) + lignes d'actions à 5 champs."""
from __future__ import annotations

import html


def create_action_row(tag: str, label: str, text: str, raw: bool = False) -> str:
    """Une ligne d'action : badge (A1…), titre, description (HTML déjà échappé si raw=True)."""
    body = text if raw else html.escape(text)
    return (f'<div class="reco-row"><span class="reco-tag">{html.escape(tag)}</span>'
            f'<span class="reco-text"><span class="rt">{html.escape(label)}</span>{body}</span></div>')


def create_priority_card(icon_html: str, title: str, title_color: str, badge: str, actions: list[tuple[str, str, str]], tip: str = "") -> str:
    """HTML d'une carte de priorité. `actions` : liste de (badge, titre, HTML de description)."""
    rows = "".join(create_action_row(*a, raw=True) for a in actions)
    return (f'<div class="reco-card"><div class="reco-head"><div class="reco-ico">{icon_html}</div>'
            f'<span class="reco-title" style="color:{title_color}">{html.escape(title)}</span>'
            f'<span class="reco-badge">{html.escape(badge)}</span>{tip}</div><div class="reco-rows">{rows}</div></div>')
