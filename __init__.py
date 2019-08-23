from flask import render_template
import os

from CTFd.models import Users, Challenges
from sqlalchemy.sql import and_
from CTFd.utils.scores import get_standings
from CTFd.utils.plugins import override_template
from CTFd.utils import get_config
from CTFd.utils.modes import TEAMS_MODE
from CTFd.utils import config



def get_user_solves(user_id):
    user = Users.query.filter_by(id=user_id).first_or_404()
    solves = user.get_solves(admin=True)
    if get_config("user_mode") == TEAMS_MODE:
        if user.team:
            all_solves = user.team.get_solves(admin=True)
        else:
            all_solves = user.get_solves(admin=True)
    else:
        all_solves = user.get_solves(admin=True)
    return all_solves


def get_user_scores_for_each_category(user_id, categories):
    all_solves = get_user_solves(user_id)
    scores_list = [0 for category in categories]
    for solve in all_solves:
        scores_list[categories.index(solve.challenge.category)] += solve.challenge.value
    return scores_list


def get_all_categories():
    challenges = (
        Challenges.query.filter(
            and_(Challenges.state != "hidden", Challenges.state != "locked")
        )
            .order_by(Challenges.value)
            .all()
    )
    categories_list = []
    for challenge in challenges:
        if not challenge.category in categories_list:
            categories_list.append(challenge.category)
    return categories_list


def load(app):
    def view_single_rank():
        # override templates
        dir_path = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(dir_path, 'assets')
        template_path = os.path.join(template_path, 'scoreboard.html')
        override_template("scoreboard.html", open(template_path).read())

        # get categories
        categories = get_all_categories()

        # load scores
        standings = get_standings()

        ranks = []
        for index1, category in enumerate(categories):
            ranks.append([])
            for standing in standings:
                account_id = standing.account_id
                name = standing.name
                oauth_id = standing.oauth_id
                score = get_user_scores_for_each_category(standing.account_id, categories)[index1]
                ranks[index1].append([account_id, name, oauth_id, score])
            ranks[index1]=sorted(ranks[index1], key=(lambda x: x[3]), reverse=True)

        # rank[0] account_id
        # rank[1] name
        # rank[2] oauth_id
        # rank[3] score

        return render_template("scoreboard.html", categories=categories, enumerate=enumerate, ranks=ranks, standings=standings, score_frozen=config.is_scoreboard_frozen())

    app.view_functions['scoreboard.listing'] = view_single_rank