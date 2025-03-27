# -*- coding: utf-8 -*-
###################################################################################

###################################################################################

from datetime import date, datetime

from odoo import api, fields, models


class SpaSequenceUpdater(models.Model):
    _name = 'spa.sequence.updater'
    _description = 'Spa Sequence Updater'

    spa_sequence = fields.Char(string="Spa Sequence")


class SpaChair(models.Model):
    _name = 'spa.chair'
    _description = 'Spa Chair'

    name = fields.Char(
        string="Chair/Bed", required=True,
        default=lambda self: self.env['spa.sequence.updater'].browse(
            1).spa_sequence or "Chair-1")
    number_of_orders = fields.Integer(string="No.of Orders")
    collection_today = fields.Float(string="Today's Collection")
    user_id = fields.Many2one(
        'hr.employee', string="User", readonly=True,
        help="""You can select the user from the Users Tab. 
        Last user from the Users Tab will be selected as the Current User.""")
    date = fields.Datetime(string="Date", readonly=True)
    user_line = fields.One2many(
        'spa.chair.user', 'spa_chair_id', string="Users")
    total_time_taken_chair = fields.Float(string="Time Reserved(Hrs)")
    active_booking_chairs = fields.Boolean(string="Active booking chairs")
    chair_created_user = fields.Integer(string="Spa Chair Created User",
                                        default=lambda self: self._uid)

    @api.model
    def create(self, values):
        """
        add sequence for chair, start date and end date on creating record
        """
        sequence_code = 'spa.chair.sequence'
        sequence_number = self.env['ir.sequence'].next_by_code(sequence_code)
        self.env['spa.sequence.updater'].browse(1).write(
            {'spa_sequence': sequence_number})
        if 'user_line' in values.keys():
            if values['user_line']:
                date_changer = []
                for elements in values['user_line']:
                    date_changer.append(elements[2]['start_date'])
                number = 0
                for elements in values['user_line']:
                    number += 1
                    if len(values['user_line']) == number:
                        break
                    elements[2]['end_date'] = date_changer[number]
                values['user_id'] = values['user_line'][len(
                    (values['user_line'])) - 1][2]['user_id']
                values['date'] = values['user_line'][len(
                    (values['user_line'])) - 1][2]['start_date']
        return super(SpaChair, self).create(values)

    def write(self, values):
        """
        add sequence for chair, start date and end date on editing record
        """
        if 'user_line' in values.keys():
            if values['user_line']:
                date_changer = []
                for elements in values['user_line']:
                    if str(elements[1]).startswith('v'):
                        date_changer.append(elements[2]['start_date'])
                number = 0
                num = 0
                for records in self.user_line:
                    if records.end_date is False:
                        if date_changer:
                            records.end_date = date_changer[0]
                for elements in values['user_line']:
                    number += 1
                    if elements[2] is not False:
                        num += 1
                        if len(values['user_line']) == number:
                            break
                        elements[2]['end_date'] = date_changer[num]
                values['user_id'] = values['user_line'][len(
                    (values['user_line'])) - 1][2]['user_id']
                values['date'] = values['user_line'][len(
                    (values['user_line'])) - 1][2]['start_date']
        return super(SpaChair, self).write(values)

    def collection_today_updater(self):
        """
        function to update the collection on the day for each chair
        """
        spa_chair = self.env['spa.chair']
        for values in self.search([]):
            chair_obj = spa_chair.browse(values.ids)
            invoiced_records = chair_obj.env['spa.order'].search(
                [('stage_id', 'in', [3, 4]), ('chair_id', '=', chair_obj.id)])
            total = 0
            for rows in invoiced_records:
                invoiced_date = str(rows.date)
                invoiced_date = invoiced_date[0:10]
                if invoiced_date == str(date.today()):
                    total = total + rows.price_subtotal
            chair_obj.collection_today = total


class SpaChairUser(models.Model):
    _name = 'spa.chair.user'
    _description = 'Spa Chair User'

    read_only_checker = fields.Boolean(string="Checker", default=False)
    user_id = fields.Many2one('hr.employee', string="User", required=True)
    start_date = fields.Datetime(
        string="Start Time", default=fields.Datetime.now, required=True)
    end_date = fields.Datetime(string="End Time", readonly=True, default=False)
    spa_chair_id = fields.Many2one(
        'spa.chair', string="Chair/Bed", required=True, ondelete='cascade',
        index=True, copy=False)

    @api.model
    def create(self, val):
        """
        update records on adding new chair user
        """
        chairs = self.env['spa.chair'].search([])
        all_active_users = []
        for records in chairs:
            if records.user_id:
                all_active_users.append(records.user_id.id)
                records.user_id.write({'active': True})
        val['read_only_checker'] = True
        return super(SpaChairUser, self).create(val)