from odoo import models, fields, api
from datetime import datetime
import pytz

class HistoryEvent(models.Model):
    _name = 'rok.history.event'
    _description = 'History Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'title'
    _order = 'is_favorite desc, start_date desc'

    # The owner of the measurement; default to the current user
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )
    active = fields.Boolean(default=True)
    is_favorite = fields.Boolean(string="Favorite")
    start_date = fields.Date(compute='_compute_start_stop_dates', store=True)
    stop_date = fields.Date(compute='_compute_start_stop_dates', store=True)
    title = fields.Char()
    info = fields.Html()
    is_disease = fields.Boolean(default=False)
    diagnosis = fields.Char()
    fact_ids = fields.One2many('rok.history.fact', 'event_id')
    categ_id = fields.Many2one('rok.history.category', string='Category')

    @api.depends('fact_ids.fact_date_time')
    def _compute_start_stop_dates(self):
        for record in self:
            if record.fact_ids:
                dates = record.fact_ids.mapped('fact_date_time')
                if dates:
                    record.start_date = min(dates).date()
                    record.stop_date = max(dates).date()
                else:
                    record.start_date = False
                    record.stop_date = False
            else:
                record.start_date = False
                record.stop_date = False

    def init_by_articles(self):
        pass

    def get_category(self, name):
        category = self.env["rok.history.category"].search([
            ("name", "=", name),
        ], limit=1)
        if not category:
            category = self.env["rok.history.category"].create({
                "name": name,
            })
        return category

    def action_migrate_news(self):
        category = self.get_category("News")
        old_records = self.env["rok.history.event"].search([
            ("categ_id", "=", category.id),
        ])
        old_records.unlink()
        articles_root = self.env["knowledge.article"].search([
            ("name", "=", "news"),
            ("parent_id", "=", False),
        ])
        if not articles_root:
            return
        articles = self.env["knowledge.article"].search([
            ("parent_id", "=", articles_root.id),
        ])
        for article in articles:
            nested_folders = article.child_ids.filtered("child_ids")
            for folder in nested_folders:
                title = f"{article.name} - {folder.name}"
                self.add_news_event(folder, category, title)
            rest_children = article.child_ids - nested_folders
            if nested_folders and not rest_children:
                continue
            self.add_news_event(article, category)
        return False

    def add_news_event(self, article, category, title=None):
        event = self.add_event(article, category, title)
        if not article.child_ids:
            event.title = article.name[18:]
            self.add_news_fact(event, article)
        else:
            for child in article.child_ids:
                self.add_news_fact(event, child)
        return event

    def add_news_fact(self, event, article):
        # Parse the datetime string
        fact_date_time = datetime.strptime(article.name[:16], "%Y-%m-%d %H:%M")

        # Apply timezone offset (+2 hours)
        # You can adjust the timezone based on your specific region
        timezone_offset = pytz.timezone('Europe/Berlin')  # +2 hours in winter, +3 in summer
        fact_date_time = timezone_offset.localize(fact_date_time)

        # Convert to UTC for storage (Odoo stores datetimes in UTC)
        fact_date_time = fact_date_time.astimezone(pytz.UTC)

        # Remove timezone info to make it naive (required by Odoo)
        fact_date_time = fact_date_time.replace(tzinfo=None)

        self.add_fact(event, fact_date_time, article.name[18:], article.body)

    def action_migrate_health(self):
        category = self.get_category("Health")
        old_records = self.env["rok.history.event"].search([
            ("categ_id", "=", category.id),
        ])
        old_records.unlink()
        articles_root = self.env["knowledge.article"].search([
            ("name", "=", "health"),
            ("parent_id", "=", False),
        ])
        if not articles_root:
            return
        articles = self.env["knowledge.article"].search([
            ("parent_id", "=", articles_root.id),
        ])
        for article in articles:
            title, _, period = article.name.partition(" [")
            start = datetime.strptime(period[:10], "%Y-%m-%d")
            if len(period) == 24:
                stop = datetime.strptime(period[13:23], "%Y-%m-%d")
            else:
                stop = start

            event = self.add_event(article, category, title=title)

            if start == stop:
                self.add_fact(event, start, "Event", article.body)
            else:
                self.add_fact(event, start, "Start of the Event", None)
                self.add_fact(event, stop, "End of the Event", None)

        return False

    def add_event(self, article, category, title=None):
        title = title or article.name
        event = self.env["rok.history.event"].create({
            "user_id": self.env.user.id,
            "title": title,
            "info": article.body,
            "categ_id": category.id,
        })
        return event

    def add_fact(self, event, fact_date_time, fact, info):
        self.env["rok.history.fact"].create({
            "event_id": event.id,
            "fact_date_time": fact_date_time,
            "fact": fact,
            "info": info,
        })

