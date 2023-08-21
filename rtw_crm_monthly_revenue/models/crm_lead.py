# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import calendar

class rtw_crm(models.Model):
    _inherit = 'crm.lead'

    def find_min_max_date_deadline(self):
        min_date = self.env['crm.lead'].search(
            [('date_deadline', '!=', False)], order='date_deadline asc', limit=1).date_deadline
        max_date = self.env['crm.lead'].search(
            [('date_deadline', '!=', False)], order='date_deadline desc', limit=1).date_deadline.replace(day=1) + timedelta(days=32)
        return min_date, max_date


    @api.onchange('expected_revenue','date_deadline')
    def compute_monthly_revenue(self):
        min_date, max_date = self.find_min_max_date_deadline()
        # num_months = (max_date.year - min_date.year) * \
        #     12 + max_date.month - min_date.month
        leads = self.search([])
        current_date = min_date
        while current_date <= max_date:
            next_month = current_date.replace(day=1) + timedelta(days=32)
            end_of_month = current_date.replace(day=1)
            print('>>>>>>>>>>>>>>>>>>> current_date' , (current_date.replace(day=1)+ timedelta(days=32) -timedelta(days=365)).replace(day=1))
            print('>>>>>>>>>>>>>>>>>>> end_of_month' , (end_of_month + timedelta(days=32)).replace(day=1))
            leads_in_month = self.env['crm.lead'].search([
                ('date_deadline', '>=', (current_date.replace(day=1)+ timedelta(days=32) -timedelta(days=365)).replace(day=1)),
                ('date_deadline', '<', (end_of_month + timedelta(days=32)).replace(day=1) ),
                ('active' ,'=',True),
                ('type','=','opportunity')
            ])
            for lead in leads_in_month:
                print('>>>>>>>>>>' , lead.stage_id.name)
            revenue_in_month = sum(leads_in_month.filtered(lambda lead: lead.stage_id.name == '受注成立').mapped('expected_revenue'))
            existed_monthly_record = self.env['rtw_crm.monthly.revenue'].search([('date', '=', current_date.replace(day=1))])
            if existed_monthly_record:
                existed_monthly_record.total_revenue = revenue_in_month
            else:
                self.env['rtw_crm.monthly.revenue'].create({
                    'date': current_date.replace(day=1),
                    'total_revenue': revenue_in_month
                })
            current_date = next_month

    def write(self , vals):
        result = super(rtw_crm,self).write(vals)
        self.refresh()
        min_date, max_date = self.find_min_max_date_deadline()
        # num_months = (max_date.year - min_date.year) * \
        #     12 + max_date.month - min_date.month
        leads = self.search([])  # Lấy tất cả bản ghi
        current_date = min_date
        while current_date <= max_date:
            next_month = current_date.replace(day=1) + timedelta(days=32)
            end_of_month = current_date.replace(day=1)
            print('>>>>>>>>>>>>>>>>>>> current_date' , (current_date.replace(day=1)+ timedelta(days=32) -timedelta(days=365)).replace(day=1))
            print('>>>>>>>>>>>>>>>>>>> end_of_month' , end_of_month)
            leads_in_month = self.env['crm.lead'].search([
                ('date_deadline', '>=', (current_date.replace(day=1)+ timedelta(days=32) -timedelta(days=365)).replace(day=1)),
                ('date_deadline', '<', (end_of_month + timedelta(days=32)).replace(day=1)),
                ('active' ,'=',True),
                ('type','=','opportunity')
            ])
            revenue_in_month = sum(leads_in_month.filtered(lambda lead: lead.stage_id.name == '受注成立').mapped('expected_revenue'))
            existed_monthly_record = self.env['rtw_crm.monthly.revenue'].search([('date', '=', current_date.replace(day=1))])
            if existed_monthly_record:
                existed_monthly_record.total_revenue = revenue_in_month
            else:
                self.env['rtw_crm.monthly.revenue'].create({
                    'date': current_date.replace(day=1),
                    'total_revenue': revenue_in_month
                })
            current_date = next_month

        return result

    def init(self):
        super(rtw_crm, self).init()
        self.compute_monthly_revenue()


class MonthlyRevenue(models.Model):
    _name = 'rtw_crm.monthly.revenue'
    _description = 'Monthly Revenue'

    date = fields.Date(string='年月')
    display_date = fields.Char(string='display 年月',compute="_compute_date")
    total_revenue = fields.Float(string='売上金額合計')

    def _compute_date(self):
        for record in self:
            record.display_date = record.date.strftime('%Y/%m')
