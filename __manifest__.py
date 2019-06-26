{
    'name': "工作管理",

    'summary': """
        人员工作情况管理,及时统计人员信息.""",

    'description': """
        人员工作情况管理，明确自身任务，方便leader预览，及时调整工作，合理分配资源.
    """,

    'author': "Thompson",
    'website': "https://yangtiancheng.github.io/bbs.github.io/",
    'sequence': 1,
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Management',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/double_plan.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# -*- coding: utf-8 -*-
