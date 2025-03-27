# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
import json
import logging

import pytz
from datetime import datetime, time, timedelta
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo import api, fields, models
_logger = logging.getLogger(__name__)

from pytz import timezone

class SpaBooking(models.Model):
    _name = 'spa.booking'
    _description = 'Spa Booking'
    
    name = fields.Char(string="Name", compute="_compute_name", required=False)
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'),('checked-in', 'Checked-in'), ('rejected', 'Rejected'), ('invoiced', 'Invoiced')])
    phone = fields.Char(string="Phone")
    email = fields.Char(string="E-Mail")

    # Remove "required=True". check at xml instead
    # service_ids = fields.Many2one('product.template', string="Service", domain = "[('type', '=', 'service')]", required=True)
    service_ids_domain = fields.Many2many('product.product', string="Service Domain", compute="_compute_service_ids_domain") 
    service_ids = fields.Many2one('product.product', string="Service", required=True) 

    chair_id = fields.Many2one('spa.chair', string = "Chair/Bed")
    company_id = fields.Many2one('res.company', 'Company',default = lambda self: self.env.company)
    
    language_id = fields.Many2one('res.lang', 'Language', default = lambda self: self.env['res.lang'].browse(1))

    # previous order domain
    order_ids_domain = fields.Many2many('sale.order', string="Previous Order Domain", compute="_compute_order_ids_domain") 
    # previous order 
    order_ids = fields.Many2one('sale.order',string="Previous Order")
    #order_ids = fields.Many2one('sale.order',string="Previous Order",domain="['&',('state','in',('sale','done')),'&',('partner_id', '=', customer_id),('order_line.product_uom_qty','>',1)]")

    date_start = fields.Datetime(string = 'Start time', required = True, default = fields.Datetime.now)
    date_stop = fields.Datetime(string = 'End time', required = True, default = lambda self: fields.Datetime.to_string(datetime.now().replace(hour= (datetime.now().hour +2))))
    
    user_id = fields.Many2one('res.users', 'Salesperson', default = lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', "Sales Team", compute = '_compute_team_id', store = True)
    # Edited by huyendm for booking history
    # Added by thanhtd for booking subject
    subject = fields.Char(required = False)
    # End by thanhtd                                                                                 
    customer_id = fields.Many2one(
        'res.partner', string = "Customer",
        help = """If the customer is a regular customer, 
        then you can add the customer in your database""")
    # Added by thanhtd for customer display on list booking screen
    customer_display = fields.Char(required = False, compute = "_compute_customer_display")
    # End by thanhtd
    partner_id = fields.Many2one('res.partner', string = 'Staff/Specialist')
    # End by huyendm

    quantity = fields.Integer(string = 'Quantity', default = 1, stored = False)

    # End by huyendm   
    #Modified by thanhtd for displaying Staff/Specialist
    partner_ids = fields.Many2many(
        'res.partner', 'spa_booking_calendar_res_partner_rel',
        string = 'Staffs/Specialists', 
        domain = lambda self:[(('id', 'in', self.env['hr.employee'].search([('active', '=', True),('department_id.name','=','KTV')]).work_contact_id.ids))], required = True)
    
    source_id = fields.Many2one('utm.source', 'Source')
    creator = fields.Char(string = "Creator",default = lambda self: self.env.user.name)
    location = fields.Selection([('home','At Home'),('spa','At Spa')], default = 'spa')
    customer_type = fields.Selection([('experience','Experience'),('retail','Retail'),('use_previous_order','Use Previous Order'),('break_time','Break Time')],default = 'use_previous_order')
    
    undone_quantity = fields.Integer(string = "Undone Quantity"
                                     , compute = "_compute_undone_quantity" 
                                     )
    # Added by thanhtd to add some notes when bookings
    remark = fields.Text(string="Remark")
    count = fields.Integer(string='Delivery Orders'
                           , compute = '_compute_count'
                           )


    #Added by huyendm for insert data to related table for display booking with process time
    @api.model
    def create(self, vals):
        if "source_id" in vals:
            # It is draft because event/booking is created by website
            source_data = self.env["utm.source"].search([('name', '=', 'My Website')])
            if(source_data and source_data.id == vals["source_id"]):
                vals['customer_type']='retail'
                vals['state']='draft'
                
            else:
                # It is confirmed of course because event/booking is created by internal user
                vals['state']='confirmed'
                
        # add condition to check: If the website side does not transmit the 'order_id' key, it will fail to booking
        if "order_ids" in vals:   
            if vals['order_ids'] > 0:
                tmp_qty = 0;
                tmp_done_qty = 0;

                order_data = self.env['sale.order'].search([("id", "=", vals['order_ids'])])
                order_line_data = self.env['sale.order.line'].search([('order_id','=',order_data.id), ('product_id', '=', vals["service_ids"])])

                for line in order_line_data:
                    tmp_qty += line.product_uom_qty
                    tmp_done_qty += line.done_qty # no "+=" line.done_qty = count from spa.order.process.times

                vals['quantity'] = tmp_qty
                vals['undone_quantity'] = tmp_qty - tmp_done_qty

                #vals['quantity'] = order_line_data.product_uom_qty
                #vals['undone_quantity'] = self.quantity - order_line_data.done_qty

        record = super(SpaBooking, self).create(vals)     
        if record.date_start >= record.date_stop:
            raise ValidationError(_('End time must be after Start time')) 
        
        return record
    #End by huyendm  

    #Added by thanhtd for override some data
    def write(self, vals):
        _logger.debug("writebythanhtd>>vals=: %s", str(vals))
        # Customer type is different than use_previous_order, order_ids is false & read-only and not update it in DB
        # Override order_ids to update it in DB
        if "customer_type" in vals and vals["customer_type"] != "use_previous_order":
            vals["order_ids"] = False
        _logger.debug("writebythanhtd>>vals=: %s", str(vals))

        write_values = super(SpaBooking, self).write(vals)
        return write_values
    #End by thanhtd
           
    def action_checkin_booking(self):
        # """
        # approve booking for spa services
        # """
        current_order_line_data = False
        # use previous order
        if self.order_ids.id > 0:
            tmp_qty = 0
            tmp_done_qty = 0
                            
            order_line_data = self.env['sale.order.line'].search([("order_id", "=", self.order_ids.id), ("product_id", "=", self.service_ids.id)])
            #quantity = order_line_data.product_uom_qty
            for line in order_line_data:
                tmp_qty += line.product_uom_qty
                tmp_done_qty += line.done_qty # no "+=" line.done_qty = count from spa.order.process.times
            # get current order line data
            for line in order_line_data:
                if(line.done_qty < line.product_uom_qty):
                    # current_order_line_data.append(line)
                    current_order_line_data = line
                    break

            #if order_line_data.done_qty >= quantity:
            if tmp_done_qty >= tmp_qty:
                raise ValidationError(_("Over quantity!"))
            else:
                # count for times_no
                count = self.get_number_process_times(self.order_ids, self.service_ids)

                order_process_time_data = {
                    'spa_order_id': self.order_ids.id,
                    'time_start': fields.Datetime.now(),
                    'times_no': count + 1,
                    'product_id': self.service_ids.id,
                    'partner_ids':self.partner_ids,
                    'spa_order_line_id': current_order_line_data.id
                }
                self.env['spa.order.process.times'].create(order_process_time_data)    

            # self.state = "checked-in"
            #     # set state = invoiced because of already paid at previous order
            self.state = "invoiced"
        else:
            # create record in sale order
            sale_order_data = {
                'partner_id': self.customer_id.id,                                               
                'date_order': fields.Datetime.now(),
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'company_id': self.company_id.id,
                'source_id': self.source_id.id, 
                'booking_id': self.id,                                          
            }
            
            sale_order = self.env['sale.order'].create(sale_order_data)

            # Assign order_ids only when Customer Type="use previous order"
            if self.customer_type == "use_previous_order":
                self.order_ids=sale_order  


            # For getting extra price
            ptav = self.env["product.template.attribute.value"].search([("id", "=", self.service_ids.combination_indices)])
            # Get duration name
            duration = self.env["product.attribute.value"].search([("id", "=", ptav.product_attribute_value_id.id)])

            #create record in sale order line
            service_data = {
                'product_uom': '1',                    
                'product_id': self.service_ids.id,
                'name': self.service_ids.name + ' (' + duration.name + ')',
                'product_uom_qty': self.quantity,
                'order_id': sale_order.id,
                'customer_lead': 0.0,
                'price_unit': self.service_ids.list_price + ptav.price_extra,
            }
            current_order_line_data = self.env['sale.order.line'].create(service_data)     
            for rec in self:
                order_process_time_data = {
                        'spa_order_id': sale_order.id,
                        'time_start': fields.Datetime.now(),
                        'times_no': 1,
                        'product_id': self.service_ids.id,
                        'partner_ids':rec.partner_ids,
                        'spa_order_line_id': current_order_line_data.id
                    }
                self.env['spa.order.process.times'].create(order_process_time_data) 
            self.state = "checked-in"
            # Return order in order to use in check in/payment
            return sale_order
        
    def action_reject_booking(self):
        """
        reject booking for spa services
        """
        template = self.env.ref(
            'spa_management.mail_template_spa_rejected')
        self.env['mail.template'].browse(template.id).send_mail(self.id,
                                                                force_send=True)
        self.state = "rejected"
        
    # Add by truongnn for add button check-in/payment
    def action_payment_booking(self):   
        """
        - Check in
        - Payment
        """
        # if not checked-in, then check-in
        # else get checked-in order to payment
        sale_order = False
        if(self.state !='checked-in'):
            _logger.debug("Not checked-in >>>: %s", self.state)  
            sale_order = self.action_checkin_booking()
        else:
            # get order checked-in
            
            sale_order = self.env["sale.order"].search([('booking_id', '=', self.id)])
            _logger.debug("Checked-in >>>: %s", self.state)
               
        _logger.debug("checked-in order.id: %s", sale_order.id)  
        action= {
            'res_model':'sale.order',
            'res_id':sale_order.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            # 'view_id':self.env.ref('spa_management.spa_order_view_form').id
            }
        self.env.cr.commit()
        return action 
    #  end by truongnn 

    # Add button for display order screen when click button order
    def action_order_view(self):
        sale_order = False
        if self.order_ids:
            _logger.debug("Not checked-in >>>: %s", self.state)  
            sale_order = self.order_ids
        else:
            # get order checked-in
            
            sale_order = self.env["sale.order"].search([('booking_id', '=', self.id)])
            _logger.debug("Checked-in >>>: %s", self.state)
               
        _logger.debug("checked-in order.id: %s", sale_order.id)  
        action= {
            'res_model':'sale.order',
            'res_id':sale_order.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            # 'view_id':self.env.ref('spa_management.spa_order_view_form').id
            }
        self.env.cr.commit()
        return action 
    
    #add by truongnn for add button confirm
    @api.constrains('customer_id')
    def action_confirm_booking(self):
        # required to customer while in draft state
        for rec in self:
            if rec.state == 'draft':
                if rec.customer_id.id == False:
                    # raise ValidationError(_('Invalid fields: Customer'))
                    message = "Cusomter/Khách hàng"
                    notification = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Invalid fields:'),
                            'type':'danger',
                            'message': (_(message)),                    
                        }
                    }
                    return notification
                else:
                    self.state = "confirmed" 
       
    #end by truongnn   

    @api.model
    def get_booking_count(self, company):
        _logger.debug("get_booking_count>>company_ids=: %s", str(company["company_ids"]))
        spa_bookings = self.env['spa.booking'].search_count([('state', 'in', ['draft', 'confirmed']),('company_id', 'in', company["company_ids"])])

        dt_start = pytz.timezone(self.env.user.tz).localize(datetime.combine(datetime.today(), time(0, 0, 0))).astimezone(pytz.UTC).replace(tzinfo=None)
        dt_end = pytz.timezone(self.env.user.tz).localize(datetime.combine(datetime.today(), time(23, 59, 59))).astimezone(pytz.UTC).replace(tzinfo=None)
        spa_bookings_today = self.env['spa.booking'].search_count(
            [
                ('state', 'in', ['draft', 'confirmed']), 
                ('date_start','>=',dt_start.strftime("%Y-%m-%d %H:%M:%S")),
                ('date_start','<=',dt_end.strftime("%Y-%m-%d %H:%M:%S")),
                ('company_id', 'in', company["company_ids"])
            ])

        #_logger.debug("datetime.utcnow(): %s", datetime.utcnow())

        # recent_works: state = sale and done
        recent_works = self.env['sale.order'].search_count([('state', 'in', ['sale','done']), ('company_id', 'in', company["company_ids"])])
        spa_orders = self.env['sale.order'].search_count([('company_id', 'in', company["company_ids"])])
       

        spa_clients = self.env['res.partner'].search_count([('partner_spa', '=', True)])

        spa_chairs = self.env['spa.chair'].search([])
        values = {
            'bookings': spa_bookings,
            'bookings_today': spa_bookings_today,
            'sales': recent_works,
            'orders': spa_orders,
            'clients': spa_clients,
            'chairs': spa_chairs
        }
        
        # print(values)
        return values

    #====================== Compute methods ======================
    # Count the number of Orders of the current booking
    def _compute_count(self):
        
            for booking in self:
                order = False
                if booking.order_ids:
                    order = booking.order_ids
                else:
                    order = self.env["sale.order"].search([('booking_id', '=', self.id)])
            booking.count = self.env['sale.order'].search_count([('id', '=', order.id)])

    def _compute_undone_quantity(self):
        for booking in self:
            if booking.order_ids:
                order_id = self.env['sale.order'].search([('id','=',booking.order_ids.id)])
            elif booking.id:
                order_id = self.env['sale.order'].search([('booking_id','=',booking.id)])
            else:
                order_id = False

            number_of_process_times = self.get_number_process_times(order_id, booking.service_ids)        
            booking.undone_quantity = booking.quantity - number_of_process_times

           
    # Added by huyendm for changing title of calendar event 
    @api.depends('customer_id')
    def _compute_name(self):
        service_name =""
        customer_name =""
        for each in self:
            convert_start = pytz.utc.localize(each.date_start).astimezone(timezone('Asia/Ho_Chi_Minh'))
            convert_end = pytz.utc.localize(each.date_stop).astimezone(timezone('Asia/Ho_Chi_Minh')) 
            time_start = datetime.strftime(convert_start, "%H:%M") 
            time_end = datetime.strftime(convert_end, "%H:%M")
            if each.service_ids:
                for data in each.service_ids:
                    service_name  += " " + str(data.name)  
            if each.customer_id and each.customer_id.name:
                customer_name = " | " + str(each.customer_id.name)
            else:
                customer_name = " | " + str(each.subject)
            each.name = time_start + " - " + time_end + customer_name + " |" + service_name  
            service_name ="" 
    # End by huyendm
    

    # Added by thanhtd for customer display on list booking screen
    @api.depends('customer_id')
    def _compute_customer_display(self):
        for record in self:
            if(record.customer_id.id):
                record.customer_display = record.customer_id.name
            else:
                record.customer_display = record.subject
    # End by thanhtd

    # Added by thanhtd for Sales Team
    @api.depends('user_id')
    def _compute_team_id(self):
        for record in self:
            if record.user_id.id:
                user_id = record.user_id.id
                user_data = self.env["res.users"].search([("id", "=", user_id)])
                record.team_id = self.env["crm.team"].search([("id", "=", user_data.sale_team_id.id)])
    # End by thanhtd


    @api.depends('order_ids')
    def _compute_service_ids_domain(self):
        self.show_previous_order_name(self.order_ids)

    @api.depends('customer_id', 'customer_type')
    def _compute_order_ids_domain(self):
        self.order_ids_domain = False
        order_ids = []

        if self.customer_id and self.customer_type == 'use_previous_order':
            order_data = self.env['sale.order'].search([('state','in',('sale','done')),('partner_id', '=', self.customer_id.id)])
            
            for data in order_data:
                for line in data.order_line:
                    # if not spent completely
                    if(line.product_id.type == "service" and line.product_id.available_booking  
                       and line.done_qty < int(line.product_uom_qty) and (data.id not in order_ids)):
                        order_ids.append(data.id)

            if order_ids:
                self.order_ids_domain = order_ids

    #====================== onchange methods ======================
    # Added by thanhtd for filling phone, email when changing customer_id
    @api.onchange('customer_id')
    def on_change_customer(self):
        for record in self:
            if record.customer_id:
                _logger.debug("on_change_customer: %s", str(record.customer_id))
                record.phone = record.customer_id.phone 
                record.email = record.customer_id.email 

                # Display mobile info when customer's phone info is not available
                if not record.customer_id.phone:
                     record.phone = record.customer_id.mobile 
                                                
    # End by thanhtd

    # Added by thanhtd if Duration is selected, date_start is changed, 
    # Re-calculate End time = Start time + duration
    @api.onchange('service_ids', 'date_start')
    def calculate_end_time(self):
        for record in self:
            ptav = self.env["product.template.attribute.value"].search([("id", "=", record.service_ids.combination_indices)])
            duration_id = self.env["product.attribute.value"].search([("id", "=", ptav.product_attribute_value_id.id)])
            
            if duration_id and record.date_start:
                    duration_name = duration_id.name.strip()
                    # slit "XXX YYY" to get XXX (minutes)
                    duration_split = duration_name.split(" ")

                    #
                    time = int(duration_split[0])
                    time_unit = duration_split[1]
                    # Filter duration by minutes or phút
                    if(time_unit.lower() == "minutes" or time_unit.lower() == "phút"):
                        # convert minutes to seconds
                        time = time * 60
                        # 0 <= seconds < 3600*24 (the number of seconds in one day) 
                        record.date_stop =  record.date_start + timedelta(seconds = time) 
    # End by thanhtd
    #     
    @api.onchange('order_ids', 'service_ids')
    def _onchange_order_ids_service_ids(self):
        if self.order_ids:
            if self.service_ids:
                order_line_data = self.env['sale.order.line'].search([("order_id", "=", self.order_ids.id), ("product_id", "=", self.service_ids.id)])

                self.quantity = 0
                tmp_done_qty = 0
                # In case 1 order has 2 lines with same service name (eg. buy 10 get 3 = 13 of quantity case)
                # Service 01, qty = 10, unit price = X, Total = Y
                # Service 01, qty = 3, unit price = 0, Total = 0
                # => Service0 1, qty = 13, unit price = X, Total = Y
                for line in order_line_data:
                    self.quantity += line.product_uom_qty
                    #tmp_done_qty += line.done_qty
                    tmp_done_qty += line.done_qty # no "+=" line.done_qty = count from spa.order.process.times

                self.undone_quantity = self.quantity - tmp_done_qty

                #self.quantity = order_line_data.product_uom_qty
                #self.undone_quantity = self.quantity - order_line_data.done_qty

                # Set user_id, team_id
                self.user_id = self.order_ids.user_id.id
                self.team_id = self.order_ids.team_id.id


    # add by truongnn
    @api.onchange('customer_type')
    def _onchange_customer_type(self):
        for rec in self:
            #  Set quantity = 1 when change Customer type != use_previous_order
            if rec.customer_type and rec.customer_type != "use_previous_order":
                rec.quantity = 1
                rec.order_ids = False   
    #end by truongnn

    # Added by thanhtd
    # If a customer is chosen and "use previous order" is chosen also
    # The first of "Order" value should be chosen automatically
    @api.onchange('customer_id', 'customer_type')
    def _onchange_customer_id_type(self):
        for rec in self:
            #if not rec.order_ids:
            #    rec.order_ids = False
            if rec.customer_id:
                if rec.customer_type and rec.customer_type == "use_previous_order":
                    order_data = self.env['sale.order'].search([('state','in',('sale','done')),('partner_id', '=', rec.customer_id.id)])
                    if order_data: #and order_data.ids:
                        #rec.order_ids = order_data.ids[0] # Temp set previous order (temp because order_data í empty after filter in show_previous_order_name())
                        previous_order_data = self.show_previous_order_name(order_data)

                        # if not exist previous_order_data, remove relative data
                        if previous_order_data:
                            rec.order_ids = previous_order_data
                        else:    
                            rec.order_ids = False
                            rec.service_ids = False
                            rec.quantity = 1                                
                    else:
                        rec.order_ids = False
                        rec.service_ids = False
                        rec.quantity = 1
    #End by thanhtd

    #====================== Private methods ======================
    # get done quantity from order_id field
    def get_number_process_times(self, order_id, service_id):         
        if order_id and service_id:
            return self.env['spa.order.process.times'].search_count( [('spa_order_id', '=',order_id.id),(('product_id', '=', service_id.id))])
        else:
            return 0
        
    # Get and display some data of previous order
    def show_previous_order_name(self, orders = None):
        # Service list
        service_ids = []
        previous_orders = []

        if orders:
            #product_data = self.order_ids.order_line.product_id.ids
            #f product_data:
            for order in orders: 
                #order_lines = self.order_ids.order_line
                #service_ids = []
                for line in order.order_line:
                    # line.done_qty, '<', int(line.product_uom_qty
                    if(line.product_id.type == "service" and line.product_id.available_booking and line.done_qty < int(line.product_uom_qty)):
                            product  = line.product_id.id
                            service_ids.append(product)

                            if order.id not in previous_orders:
                                previous_orders.append(order.id)

            # Set for displaying in list            
            self.service_ids_domain = service_ids

            # Check if not exist (from DB). Set for displaying first value
            if not self.id and service_ids:
                self.service_ids = service_ids[0]  # Set Previous order service        

        else:
            #self.service_ids = False
            self.service_ids_domain = self.env["product.product"].search([('type', '=', 'service'),('available_booking', '=', 'True')])
        
        # return 1: has previous order data
        if service_ids:
            return previous_orders[0]
        else:
            return 0        