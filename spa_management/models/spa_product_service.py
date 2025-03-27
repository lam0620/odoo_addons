# -*- coding: utf-8 -*-
###################################################################################

###################################################################################

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    available_booking = fields.Boolean(string = "Can be Booked")