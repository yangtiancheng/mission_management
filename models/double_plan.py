# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, modules
from odoo.exceptions import ValidationError
import datetime

DATE_FORMAT = "%Y-%m-%d"


class DoublePlans(models.Model):
    """
    任务管理头
    """
    _name = 'double.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # 标题
    name = fields.Char(string='日报内容', default='日报内容', readonly=True)
    # 年度
    year = fields.Char(string='年度', readonly=True, track_visibility='onchange')
    # 月份
    month = fields.Selection([('01', '1月'),
                              ('02', '2月'),
                              ('03', '3月'),
                              ('04', '4月'),
                              ('05', '5月'),
                              ('06', '6月'),
                              ('07', '7月'),
                              ('08', '8月'),
                              ('09', '9月'),
                              ('10', '10月'),
                              ('11', '11月'),
                              ('12', '12月')],
                             string='月份', help='月份', readonly=True, track_visibility='onchange')
    # 周次
    week = fields.Selection([('1', '第1周'),
                             ('2', '第2周'),
                             ('3', '第3周'),
                             ('4', '第4周'), ],
                            string='周次', help='周次', track_visibility='onchange')
    # 员工
    employee_id = fields.Many2one(comodel_name='hr.employee', string='技术顾问', readonly=True, track_visibility='onchange')
    # 登录者是当前单据员工的直系经理
    is_manager = fields.Boolean(compute='_judge_is_manager')
    # 登录者是当前单据员工
    is_self = fields.Boolean(compute='_judge_is_manager')
    # 状态
    state = fields.Selection([('created', '维护中'),
                              ('confirm', '已确认'),
                              ('done', '已关闭')],
                             string='状态', help='状态', default='created', track_visibility='onchange')
    # 周计划详细内容
    double_plan_ids = fields.One2many(comodel_name='double.plan.line', inverse_name='head_id')
    # 下周计划
    double_next_plan_ids = fields.One2many(comodel_name='double.next.plan.line', inverse_name='head_id')

    # - 组长职能
    # 上级评价
    star_rating = fields.Selection([
        ('1', '⭐️'),
        ('2', '⭐⭐'),
        ('3', '⭐⭐⭐'),
        ('4', '⭐⭐⭐⭐'),
        ('5', '⭐⭐⭐⭐⭐')],
        string='上级评价', help='上级评价')
    # 上级评价
    leader_comment = fields.Html(string='组长评语')

    _sql_constraints = [
        ('year_month_and_week', 'unique(year, month, week, create_uid)', '年-月-周 每个用户唯一!')
    ]

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.env.user.id == rec.create_uid.id:
                pass
            else:
                raise ValidationError(_('您仅可以删除自己创建的单据!'))
            if rec.state == 'confirm' or rec.state == 'done':
                raise ValidationError(_('您仅可以删除维护中的单据!'))
        return super(DoublePlans, self).unlink()

    @api.model
    def default_get(self, fields):
        result = super(DoublePlans, self).default_get(fields)
        result['year'] = str(datetime.datetime.today())[:4]
        result['month'] = str(datetime.datetime.today())[5:7]
        result['employee_id'] = self.env.user.employee_ids and self.env.user.employee_ids[0].id or False
        return result

    @api.one
    @api.depends('employee_id')
    def _judge_is_manager(self):
        if self.employee_id:
            if self.employee_id.parent_id and self.env.user.employee_ids and self.employee_id.parent_id.id == self.env.user.employee_ids[0].id:
                self.is_manager = True
            else:
                self.is_manager = False

            if self.env.user.employee_ids and self.employee_id.id == self.env.user.employee_ids[0].id:
                self.is_self = True
            else:
                self.is_self = False

    @api.multi
    def button_confirm(self):
        for res in self:
            if len(res.double_plan_ids) == 0:
                raise ValidationError(_('请确认周内日报信息已维护！'))
            res.state = 'confirm'

    @api.multi
    def button_done(self):
        for res in self:
            if self.env.user.employee_ids and self.env.user.employee_ids[0].id == res.employee_id.parent_id.id:
                res.state = 'done'
            else:
                pass

    @api.multi
    def button_restart(self):
        for res in self:
            if self.env.user.employee_ids and self.env.user.employee_ids[0].id == res.employee_id.parent_id.id:
                res.state = 'created'
            else:
                pass


class DoublePlansLine(models.Model):
    _name = 'double.plan.line'
    # 星期几

    name = fields.Selection([('1', '星期一'),
                             ('2', '星期二'),
                             ('3', '星期三'),
                             ('4', '星期四'),
                             ('5', '星期五'),
                             ('6', '星期六'),
                             ('7', '星期日'), ],
                            string='星期', help='星期')
    # 计划主单据
    head_id = fields.Many2one(comodel_name='double.plan', string='主单据')
    # 当前日期
    date = fields.Date(string='本周工作日期')
    # 工作时间
    work_time = fields.Char(string='工作时间(格式HH:00-HH:00)', default='9:00-21:00')
    # 工作时间量
    work_time_sum = fields.Integer(compute='_compute_work_time', string='合计')
    # 工作内容
    work_content = fields.Char(string='工作内容')
    # 备注
    note = fields.Char(string='备注')
    # 工作内容
    per_work_content = fields.Char(string='次日工作')
    # 明日是否有具体开发任务
    has_rdc_mission = fields.Boolean(string='次日有开发',help='明日是否有具体的开发任务',default=False)

    _sql_constraints = [
        ('head_id_and_date', 'unique( head_id, name，date)', '本周工作行记录日期必须唯一！')
    ]

    @api.one
    @api.depends('work_time')
    def _compute_work_time(self):
        if self.work_time:
            start_datetime, end_datetime = self.work_time.split('-')
            diff_hours = int(end_datetime.split(':')[0]) - int(start_datetime.split(':')[0])
            self.work_time_sum = int(diff_hours)
        else:
            self.work_time_sum = 0

    @api.model
    def default_get(self, fields):
        result = super(DoublePlansLine, self).default_get(fields)
        # 默认星期赋值
        result['name'] = str(datetime.datetime.today().weekday() + 1)
        return result


class DoubleNextPlansLine(models.Model):
    _name = 'double.next.plan.line'

    name = fields.Selection([('1', '星期一'),
                             ('2', '星期二'),
                             ('3', '星期三'),
                             ('4', '星期四'),
                             ('5', '星期五'),
                             ('6', '星期六'),
                             ('7', '星期日'), ],
                            string='星期', help='星期')
    # 主单据记录
    head_id = fields.Many2one(comodel_name='double.plan',string='主单据')
    # 当前日期
    date = fields.Date(string='下周工作日期')
    # 预计工作内容
    work_content = fields.Char(string='预计工作内容')

    _sql_constraints = [
        ('head_id_and_date', 'unique( head_id, name，date)', '下周预期计划行记录日期必须唯一！')
    ]
