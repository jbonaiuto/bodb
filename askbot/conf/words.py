"""
General skin settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import values
from django.utils.translation import ugettext_lazy as _
from askbot.skins import utils as skin_utils
from askbot import const
from askbot.conf.super_groups import CONTENT_AND_UI

WORDS = ConfigurationGroup(
                    'WORDS',
                    _('Site terms vocabulary'),
                    super_group = CONTENT_AND_UI
                )

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASK_YOUR_QUESTION',
        default=_('Post Comment/Question'),
        description=_('Post Comment/Question'),
        help_text=_('Used on a button'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_PLEASE_ENTER_YOUR_QUESTION',
        default=_('Please enter your comment/question'),
        description=_('Please enter your comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASK_THE_GROUP',
        default=_('Post to the Group'),
        description=_('Post to the Group'),
        help_text=_('Used on a button'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_POST_YOUR_ANSWER',
        default=_('Post Your Reply/Answer'),
        description=_('Post Your Reply/Answer'),
        help_text=_('Used on a button'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWER_YOUR_OWN_QUESTION',
        default=_('Reply To Your Own Comment/Question'),
        description=_('Reply To Your Own CommentQuestion'),
        help_text=_('Used on a button'),
        localized=True
    )
)

settings.register(
    values.LongStringValue(
        WORDS,
        'WORDS_INSTRUCTION_TO_ANSWER_OWN_QUESTION',
        default=_(
            '<span class="big strong">You are welcome to reply your own comment/question</span>, '
            'but please make sure to give an <strong>answer</strong>. '
            'Remember that you can always <strong>revise your original question</strong>.'
        ),
        description=_('Instruction to reply to your own comment/questions'),
        help_text=_('HTML is allowed'),
        localized=True
    )
)

settings.register(
    values.LongStringValue(
        WORDS,
        'WORDS_INSTRUCTION_TO_POST_ANONYMOUSLY',
        default=_(
            '<span class="strong big">Please start posting anonymously</span> - '
            'your entry will be published after you log in or create a new account.'
        ),
        description=_('Instruction to post anonymously'),
        help_text=_('HTML is allowed'),
        localized=True
    )
)

settings.register(
    values.LongStringValue(
        WORDS,
        'WORDS_INSTRUCTION_TO_GIVE_ANSWERS',
        default=_(
            'Please try to <strong>give a substantial reply/answer</strong>, '
            'for discussions, <strong>please use comments</strong> and '
            '<strong>do remember to vote</strong>.'
        ),
        description=_('Instruction to give reply/answers'),
        help_text=_('HTML is allowed'),
        localized=True
    )
)

settings.register(
    values.LongStringValue(
        WORDS,
        'WORDS_INSTRUCTION_FOR_THE_CATEGORY_SELECTOR',
        default=_(
            'Categorize your question using this tag selector or '
            'entering text in tag box.'
        ),
        description=_('Instruction for the catogory selector'),
        help_text=_('Plain text only'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_EDIT_YOUR_PREVIOUS_ANSWER',
        default=_('Edit Your Previous Reply/Answer'),
        description=_('Edit Your Previous Reply/Answer'),
        help_text=_('Used on a button'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASK_QUESTIONS',
        default=_('post comments/questions'),
        description=_('post comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_POST_ANSWERS',
        default=_('post replies/answers'),
        description=_('post replies/answers'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_MERGE_QUESTIONS',
        default=_('Merge duplicate comments/questions'),
        description=_('Merge duplicate comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ENTER_DUPLICATE_QUESTION_ID',
        default=_('Enter duplicate comment/question ID'),
        description=_('Enter duplicate comment/question ID'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASKED',
        default=_('commented/asked'),
        description=_('commented/asked'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASKED_FIRST_QUESTION',
        default=_('Post first comment/question'),
        description=_('Post first comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASKED_BY_ME',
        default=_('Posted by me'),
        description=_('Posted by me'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASKED_A_QUESTION',
        default=_('Posted a comment/question'),
        description=_('Posted a comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWERED_A_QUESTION',
        default=_('Replied/answered to a comment/question'),
        description=_('Replied/answered to a comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWERED_BY_ME',
        default=_('Replied/answered by me'),
        description=_('Replied/answered by me'),
        localized=True
    )
)


settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ACCEPTED_AN_ANSWER',
        default=_('accepted a reply/answer'),
        description=_('accepted a reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GAVE_ACCEPTED_ANSWER',
        default=_('Gave accepted reply/answer'),
        description=_('Gave accepted reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWERED',
        default=_('replied/answered'),
        description=_('replied/answered'),
        localized=True
    )
)

settings.register(
    values.LongStringValue(
        WORDS,
        'WORDS_QUESTIONS_COUNTABLE_FORMS',
        default='question\nquestions',
        description=_('Countable plural forms for "comment/question"'),
        help_text=_('Enter one form per line, pay attention'),
        localized=True
    )
)

settings.register(
    values.LongStringValue(
        WORDS,
        'WORDS_ANSWERS_COUNTABLE_FORMS',
        default='answer\nanswers',
        description=_('Countable plural forms for "reply/answer"'),
        help_text=_('Enter one form per line, pay attention'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_QUESTION_SINGULAR',
        default=_('comment/question'),
        description=_('comment/question (noun, singular)'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_QUESTION_PLURAL',
        default=_('comments/questions'),
        description=_('comments/questions (noun, plural)'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_UNANSWERED_QUESTION_SINGULAR',
        default=_('unreplied comment/question'),
        description=_('unreplied comment/question (singular)'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_UNANSWERED_QUESTION_PLURAL',
        default=_('unreplied questions'),
        description=_('unreplied questions (plural)'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWER_SINGULAR',
        default=_('reply/answer'),
        description=_('reply/answer (noun, sungular)'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_QUESTION_VOTED_UP',
        default=_('Comment/Question voted up'),
        description=_('Comment/Question voted up'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWER_VOTED_UP',
        default=_('Reply/Answer voted up'),
        description=_('Reply/Answer voted up'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_UPVOTED_ANSWER',
        default=_('upvoted reply/answer'),
        description=_('upvoted reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_NICE_ANSWER',
        default=_('Nice Reply/Answer'),
        description=_('Nice Reply/Answer'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_NICE_QUESTION',
        default=_('Nice Comment/Question'),
        description=_('Nice Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GOOD_ANSWER',
        default=_('Good Reply/Answer'),
        description=_('Good Reply/Answer'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GOOD_QUESTION',
        default=_('Good Comment/Question'),
        description=_('Good Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GREAT_ANSWER',
        default=_('Great Reply/Answer'),
        description=_('Great Reply/Answer'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GREAT_QUESTION',
        default=_('Great Comment/Question'),
        description=_('Great Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_POPULAR_QUESTION',
        default=_('Popular Comment/Question'),
        description=_('Popular Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_NOTABLE_QUESTION',
        default=_('Notable Comment/Question'),
        description=_('Notable Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_FAMOUS_QUESTION',
        default=_('Famous Comment/Question'),
        description=_('Famous Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_STELLAR_QUESTION',
        default=_('Stellar Comment/Question'),
        description=_('Stellar Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_FAVORITE_QUESTION',
        default=_('Favorite Comment/Question'),
        description=_('Favorite Comment/Question'),
        help_text=_('Badge name'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_UPVOTED_ANSWERS',
        default=_('upvoted replies/answers'),
        description=_('upvoted replies/answers'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_SHOW_ONLY_QUESTIONS_FROM',
        default=_('Show only comments/questions from'),
        description=_('Show only comments/questions from'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_PLEASE_ASK_YOUR_QUESTION_HERE',
        default=_('Please post your comment/question here'),
        description=_('Please post your comment/question here'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_THIS_QUESTION_HAS_BEEN_DELETED',
        default=_(
                'Sorry, this comment/question has been '
                'deleted and is no longer accessible'
            ),
        description=_('This comment/question has been deleted'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_PLEASE_ENTER_YOUR_QUESTION',
        default=_('Please enter your comment/question'),
        description=_('Please enter your comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_DELETE_YOUR_QUESTION',
        default=_('delete your comment/question'),
        description=_('delete your comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ASK_A_QUESTION_INTERESTING_TO_THIS_COMMUNITY',
        default=_('post a comment/question interesting to this community'),
        description=_('post a comment/question interesting to this community'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_NO_QUESTIONS_HERE',
        default=_('No comments/questions here.'),
        description=_('No comments/questions here.'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_PLEASE_FOLLOW_QUESTIONS',
        default=_('Please follow some comments/questions or follow some users.'),
        description=_('Please follow some comments/questions or follow some users.'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_PLEASE_FEEL_FREE_TO_ASK_YOUR_QUESTION',
        default=_('Please feel free to post your comment/question!'),
        description=_('Please feel free to post your comment/question!'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_SWAP_WITH_QUESTION',
        default=_('swap with comment/question'),
        description=_('swap with comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_REPOST_AS_A_QUESTION_COMMENT',
        default=_('repost as a question comment'),
        description=_('repost as a question comment'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ONLY_ONE_ANSWER_PER_USER_IS_ALLOWED',
        default=_('(only one reply/answer per user is allowed)'),
        description=_('Only one reply/answer per user is allowed'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ACCEPT_BEST_ANSWERS_FOR_YOUR_QUESTIONS',
        default=_('Accept the best reply/answers for your questions'),
        description=_('Accept the best reply/answers for your questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_AUTHOR_OF_THE_QUESTION',
        default=_('author of the comment/question'),
        description=_('author of the comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ACCEPT_OR_UNACCEPT_THE_BEST_ANSWER',
        default=_('accept or unaccept the best reply/answer'),
        description=_('accept or unaccept the best reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ACCEPT_OR_UNACCEPT_OWN_ANSWER',
        default=_('accept or unaccept your own reply/answer'),
        description=_('accept or unaccept your own reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_YOU_ALREADY_GAVE_AN_ANSWER',
        default=_('you already gave a reply/answer'),
        description=_('you already gave a reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GAVE_AN_ANSWER',
        default=_('gave a reply/answer'),
        description=_('gave a reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWER_OWN_QUESTIONS',
        default=_('reply/answer own comment/questions'),
        description=_('reply/answer own comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWERED_OWN_QUESTION',
        default=_('Replied/Answered own comment/question'),
        description=_('Replied/Answered own comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_REPOST_AS_A_COMMENT_UNDER_THE_OLDER_ANSWER',
        default=_('repost as a comment under older comment/answer'),
        description=_('repost as a comment under older comment/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_INVITE_OTHERS_TO_HELP_ANSWER_THIS_QUESTION',
        default=_('invite other to help reply/answer this comment/question'),
        description=_('invite other to help reply/answer this comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_RELATED_QUESTIONS',
        default=_('Related comments/questions'),
        description=_('Related comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_QUESTION_TOOLS',
        default=_('Comment/Question Tools'),
        description=_('Comment/Question Tools'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_THIS_QUESTION_IS_CURRENTLY_SHARED_ONLY_WITH',
        default=_('Phrase: this comment/question is currently shared only with:'),
        description=_('Phrase: this comment/question is currently shared only with:'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_BE_THE_FIRST_TO_ANSWER_THIS_QUESTION',
        default=_('Be the first one to reply/answer this comment/question!'),
        description=_('Be the first one to reply/answer this comment/question!'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_FOLLOWED_QUESTIONS',
        default=_('followed comments/questions'),
        description=_('followed comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_FOLLOW_QUESTIONS',
        default=_('follow comments/questions'),
        description=_('follow comments/questions'),
        help_text=_('Indefinite form'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_COMMENTS_AND_ANSWERS_TO_OTHERS_QUESTIONS',
        default = '',
        description = _('Phrase: comments and replies/answers to others comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_YOU_CAN_POST_QUESTIONS_BY_EMAILING_THEM_AT',
        default=_('You can post comments/questions by emailing them at'),
        description=_('You can post comments/questions by emailing them at'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_LIST_OF_QUESTIONS',
        default=_('List of comments/questions'),
        description=_('List of comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_COMMUNITY_GIVES_YOU_AWARDS',
        default=_('Community gives you awards for your comments/questions, replies/answers and votes'),
        description=_('Community gives you awards for your comments/questions, replies/answers and votes'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_CLOSE_QUESTION',
        default=_('Close comment/question'),
        description=_('Close comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_CLOSE_QUESTIONS',
        default=_('close comments/questions'),
        description=_('close comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_EDIT_QUESTION',
        default=_('Edit comment/question'),
        description=_('Edit comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_QUESTION_IN_ONE_SENTENCE',
        default=_('Comment/Question - in one sentence'),
        description=_('Comment/Question - in one sentence'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_RETAG_QUESTION',
        default=_('Retag comment/question'),
        description=_('Retag comment/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_RETAG_QUESTIONS',
        default=_('retag comments/questions'),
        description=_('retag comments/questions'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_REOPEN_QUESTION',
        default=_('Reopen comments/question'),
        description=_('Reopen comments/question'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_THERE_ARE_NO_UNANSWERED_QUESTIONS_HERE',
        default=_('There are no unreplied comments/questions here'),
        description=_('There are no unreplied comments/questions here'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_THIS_ANSWER_HAS_BEEN_SELECTED_AS_CORRECT',
        default=_('this reply/answer has been selected as correct'),
        description=_('this reply/answer has been selected as correct'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_MARK_THIS_ANSWER_AS_CORRECT',
        default=_('mark this reply/answer as correct'),
        description=_('mark this reply/answer as correct'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_LOGIN_SIGNUP_TO_ANSWER',
        default=_('Login/Signup to Reply/Answer'),
        description=_('Login/Signup to Reply/Answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_YOUR_ANSWER',
        default=_('Your Reply/Answer'),
        description=_('Your Reply/Answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ADD_ANSWER',
        default=_('Add Reply/Answer'),
        description=_('Add Reply/Answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GIVE_AN_ANSWER_INTERESTING_TO_THIS_COMMUNITY',
        default=_('give an reply/answer interesting to this community'),
        description=_('give an reply/answer interesting to this community'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_GIVE_A_GOOD_ANSWER',
        default=_('give a substantial reply/answer'),
        description=_('give a substantial reply/answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_TRY_TO_GIVE_AN_ANSWER',
        default=_('try to give an reply/answer, rather than engage into a discussion'),
        description=_('try to give an reply/answer, rather than engage into a discussion'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_SHOW_ONLY_SELECTED_ANSWERS_TO_ENQUIRERS',
        default=_('show only selected replies/answers to enquirers'),
        description=_('show only selected replies/answers to enquirers'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_UNANSWERED',
        default = _('UNREPLIED'),
        description = _('UNREPLIED'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_EDIT_ANSWER',
        default=_('Edit Reply/Answer'),
        description=_('Edit Reply/Answer'),
        localized=True
    )
)

settings.register(
    values.StringValue(
        WORDS,
        'WORDS_ANSWERED',
        default=_('Unreplied/Answered'),
        description=_('Unreplied/Answered'),
        localized=True
    )
)
