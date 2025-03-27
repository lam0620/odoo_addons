# -*- coding: utf-8 -*-
###################################################################################

###################################################################################

from odoo import models, fields

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'
    def name_get(self):
        return [(value.id, "%s" % (value.name)) for value in self]