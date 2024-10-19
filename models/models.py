from odoo import fields, models, api
from datetime import datetime

class SaleOrderReactPortal(models.Model):
    _inherit = 'sale.order'

    react_portal_sales_person = fields.Many2one('res.users', string='React portal sales person')

    def format_order_date(self):
        date_obj = datetime.strptime(str(self.date_order.date()), "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")

        return formatted_date
