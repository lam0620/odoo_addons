# -*- coding: utf-8 -*-
###################################################################################

###################################################################################

from datetime import date, datetime, timedelta
from odoo import api, models, fields
import logging
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    # Booking id
    booking_id = fields.Integer(string='Booking Id')

    # product, read only not to save DB
    product_id_domain = fields.Many2many('product.product', string="Service Domain", compute="_compute_product_id_domain")
    product_id_display = fields.Many2one('product.product', string="Service", domain = "[('type', '=', 'service')]", compute="_compute_product_id_display", store=False, readonly=False)
    # end
    
    # process_times
    order_process_times_ids = fields.One2many('spa.order.process.times', 'spa_order_id', string="Order Process Times", compute="_compute_order_process_times_ids")

    @api.depends('product_id_display')
    def _compute_order_process_times_ids(self):
        for order in self:
            _logger.debug("_compute_order_process_times_ids>>order_process_times!!!=: %s", str(order.order_process_times_ids))
            order.order_process_times_ids = False
            _logger.debug("_compute_order_process_times_id>>ids=: %s", str(order.ids))
            _logger.debug("_compute_order_process_times_ids>>product_id=: %s", str(order.product_id_display))
            # when change 1 field on sale order screen, order id will create temp id with format "NewId_xxx"( xxx: current order id)
            if order.ids:
                _logger.debug("_compute_order_process_times_ids>>ids[0]=: %s", str(order.ids[0]))
                _logger.debug("_compute_order_process_times_ids>>product_id=: %s", str(order.product_id_display))
                if order.product_id_display.id:
                    order_process_times = self.env['spa.order.process.times'].search( [('spa_order_id', '=', order.ids[0]),('product_id', '=', order.product_id_display.id)])
                    _logger.debug("_compute_order_process_times_ids>>order_process_times=: %s", str(order_process_times))
                    if order_process_times:
                        order.order_process_times_ids = order_process_times

    def _compute_product_id_domain(self):
        if self.order_line.ids:
            ids = self.order_line.product_id.ids
            _logger.debug("_compute_product_ids_domain>>ids=: %s", str(ids))
            self.product_id_domain = ids
        else:
            self.product_id_domain = False

    # Display first value in Service dropdown
    def _compute_product_id_display(self):
        if self.order_line.ids:
            ids = self.order_line.product_id.ids
            _logger.debug("_compute_product_id_display>>ids=: %s", str(ids))
            self.product_id_display = ids[0]
        else:
            self.product_id_display = False

    # set state record booking is invoiced when create invoice    
    def _create_invoices(self,grouped=False, final=False, date=None):
        res = super(SaleOrderInherit, self)._create_invoices(grouped=grouped, final=final, date=date)
        salon_booking = self.env['spa.booking'].search([('id', '=', self.booking_id)])
        salon_booking.write({'state' : 'invoiced'})
        return res


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    # Number of times has been done
    done_qty = fields.Integer(string='Done Qty', compute='_compute_done_qty')
    
    @api.depends('order_id','product_id')
    def _compute_done_qty(self):
        for line in self:
            line.done_qty = 0
            if line.id and line.product_id.id:
                #if line.product_id.id:
                line.done_qty = self.env['spa.order.process.times'].search_count( [('spa_order_line_id', '=', line.id),('product_id', '=', line.product_id.id)])


class SpaOrderProcessTimes(models.Model):
    _name = 'spa.order.process.times'
    _description = 'Spa Order Process Times'

    spa_order_id = fields.Many2one(
    'sale.order', string="Sale Order", required=True, ondelete='cascade',
    index=True, copy=False)

    spa_order_line_id = fields.Many2one(
        'sale.order.line', string="Sale Order Line", required=True, ondelete='cascade',
        index=True, copy=False)
    
    times_no = fields.Float(string='Sequence')
    
    time_start = fields.Datetime(string='Date', default=lambda self: self._cal_time_start())

    # product(servives)
    product_id = fields.Many2one('product.product', string="Service", domain = "[('type', '=', 'service')]")

    # Staffs/Specialists
    partner_ids = fields.Many2many('res.partner', 'spa_order_process_times_res_partner_rel', string = 'Staffs/Specialists', 
                                   domain = lambda self:[(('id', 'in', self.env['hr.employee'].search([]).work_contact_id.ids))])
    
    def _cal_time_start(self):
        now = datetime.now()
        return now