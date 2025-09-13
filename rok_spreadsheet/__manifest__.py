# -*- coding: utf-8 -*-
{
    'name': 'Spreadsheet Chart Enhancements',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Smooth lines and thin borders for Odoo spreadsheet charts',
    'description': """
        Spreadsheet Chart Enhancements
        ==================================

        This module enhances Odoo spreadsheet charts with:

        * Smooth curved lines (cubic interpolation)
        * Thin chart borders (1px width)
        * Better visual appearance

        Features:

        * Automatic smooth line rendering for all line charts
        * Thin borders for cleaner appearance
        * No configuration required - works automatically
        * Compatible with all existing dashboards
    """,
    'website': '',
    'depends': [
        'spreadsheet',
        'spreadsheet_dashboard',
    ],
    'data': [],
    'assets': {
        'spreadsheet.o_spreadsheet': [
            'rok_spreadsheet/static/src/chart/odoo_chart/rok_simple_patch.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'author': 'Ruslan Akunevich',
    'license': 'LGPL-3',
}
