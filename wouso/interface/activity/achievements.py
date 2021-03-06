from datetime import datetime, timedelta
from django.utils.translation import ugettext_noop
import logging
from wouso.core.app import App
from models import Activity
from signals import addActivity

def consecutive_seens(player, timestamp):
    """
     Return the count of consecutive seens for a player, until timestamp
    """
    activities = Activity.get_private_activity(player).filter(action='seen').order_by('-timestamp')[0:100]
    today = timestamp.date()
    for i, activity in enumerate(activities):
        date = activity.timestamp.date()
        if date != today + timedelta(days=-i):
            return i

    return len(activities)
def consecutive_qotd_correct(player):
    """
     Return the count of correct qotd in a row
    """
    activities = Activity.get_player_activity(player).filter(action__contains = 'qotd').order_by('-timestamp')[:12]
    result = 0
    for i in activities:
        if 'correct' in i.action:
            result +=1
        else:
            return result
    return result
class Achievements(App):

    @classmethod
    def earn_achievement(cls, player, modifier):
        result = player.magic.give_modifier(modifier)
        if result is not None:
            message = ugettext_noop('earned {artifact}')
            addActivity.send(sender=None, user_from=player, game=None, message=message,
                arguments=dict(artifact=result.artifact)
            )
        else:
            logging.debug('%s would have earned %s, but there was no artifact' % (player, modifier))

    @classmethod
    def activity_handler(cls, sender, **kwargs):
        action = kwargs.get('action', None)
        player = kwargs.get('user_from', None)
        if not action:
            return
        if 'qotd' in action:
            #Check 10 qotd in a row
            if consecutive_qotd_correct(player) >= 10:
                if not player.magic.has_modifier('ach-qotd-10'):
                    cls.earn_achievement(player,'ach-qotd-10')
        if action == 'seen':
            # Check previous 10 seens
            if consecutive_seens(player, datetime.now()) >= 10:
                if not player.magic.has_modifier('ach-login-10'):
                    cls.earn_achievement(player, 'ach-login-10')
    @classmethod
    def get_modifiers(self):
        return ['ach-login-10','ach-qotd-10']

def check_for_achievements(sender, **kwargs):
    Achievements.activity_handler(sender, **kwargs)

addActivity.connect(check_for_achievements)
