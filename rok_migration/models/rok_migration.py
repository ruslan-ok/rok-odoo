import os
import csv
import json
import base64
import logging
import psycopg2
import dotenv
from collections import defaultdict
from itertools import groupby
from odoo import models, api, Command, _

CSV_PATH = '/opt/project/csv'

_logger = logging.getLogger(__name__)

class RokMigration(models.AbstractModel):
    _name = 'rok.migration'
    _description = 'Rok Migration'

    @api.model
    def test_connection(self):
        dotenv.load_dotenv()
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                connect_timeout=5,
            )
        except Exception as e:
            _logger.info("Error: ", e)
            raise
        try:
            with conn.cursor() as cr:
                cr.execute("SELECT * from res_company;")
                data = cr.fetchall()
                _logger.info("Data from Database: ", data)
            return data
        finally:
            conn.close()

    @api.model
    def run_migration(self):
        self.unlink_old_data()
        data = self.load_data()
        self.migrate_account_move_lines(data)

    @api.model
    def unlink_old_data(self):
        _logger.info("[Rok Migration] Unlinking old data: start")
        items = self.env["rok.migration.items"].search([])
        item_vals = [{"res_model": item.res_model, "res_id": item.res_id} for item in items]
        def sort_order(item):
            match item["res_model"]:
                case "account.move":
                    return 0, item["res_id"]
                case "account.move.line":
                    return 99, item["res_id"]
                case _:
                    return 1, item["res_id"]
        item_vals = sorted(item_vals, key=sort_order)
        model_groups = groupby(item_vals, lambda x: x["res_model"])
        for model, items in model_groups:
            model_items = self.env[model].browse([item["res_id"] for item in items])
            if model == "account.move":
                model_items.button_draft()
            model_items.unlink()
        items.unlink()
        _logger.info("[Rok Migration] Unlinking old data: end")

    @api.model
    def load_data(self):
        _logger.info("[Rok Migration] Loading data: start")
        data = {}

        # Get all CSV files from the CSV_PATH directory
        csv_files = []
        for filename in os.listdir(CSV_PATH):
            if filename.endswith('.csv'):
                csv_files.append(filename[:-4])  # Remove .csv extension

        # Load data from all CSV files
        for file_name in csv_files:
            match file_name:
                case 'ir_attachment':
                    data[file_name] = self.load_attachments()
                case 'account_move__account_payment':
                    data[file_name] = self.load_account_move_account_payment()
                case 'account_move_line_account_tax_rel':
                    data[file_name] = self.load_account_move_line_account_tax_rel()
                case _:
                    data[file_name] = self.load_table(file_name)
        _logger.info("[Rok Migration] Loading data: end")
        return data

    @staticmethod
    def get_file_data(file_name):
        file_path = os.path.join(CSV_PATH, file_name + ".csv")
        with open(file_path, newline='', encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=",")
            header = next(reader)

            dict_reader = csv.DictReader(f, fieldnames=header, delimiter=",")
            for row in dict_reader:
                yield row

    @api.model
    def load_table(self, name):
        table_data = {}
        for row in self.get_file_data(name):
            table_data[row["id"]] = row
        return table_data

    @api.model
    def load_attachments(self):
        attachments = defaultdict(list)
        for row in self.get_file_data("ir_attachment"):
            key = (row["res_model"], row["res_id"])
            attachments[key].append(row)
        return attachments

    @api.model
    def load_account_move_account_payment(self):
        table_data = []
        for row in self.get_file_data("account_move__account_payment"):
            table_data.append(row)
        return table_data

    @api.model
    def load_account_move_line_account_tax_rel(self):
        table_data = defaultdict(list)
        for row in self.get_file_data("account_move_line_account_tax_rel"):
            table_data[row["account_move_line_id"]].append(row["account_tax_id"])
        return table_data


    @api.model
    def fix(self, records):
        model = records._name
        vals = [{"res_model": model, "res_id": record.id} for record in records]
        self.env["rok.migration.items"].create(vals)
        return records

    @api.model
    def copy_attachments(self, data, res_model, res_id, new_object):
        attachments = data["ir_attachment"]
        image_1920 = None
        att_files = []
        for attachment in attachments[(res_model, res_id)]:
            match attachment["res_field"]:
                case "image_1920":
                    image_1920 = attachment
                case "":
                    att_files.append(attachment)

        src_path = "/workspace/rok_odoo"

        if image_1920 and image_1920.get("store_fname"):
            src_file = os.path.join(src_path, image_1920["store_fname"])
            if os.path.exists(src_file):
                with open(src_file, "rb") as f:
                    new_object.image_1920 = base64.b64encode(f.read())

        def _create_ir_attachment(att, res_model, res_id):
            with open(os.path.join(src_path, att["store_fname"]), "rb") as f:
                file_content = f.read()
            vals = {
                "name": att["name"],
                "res_model": res_model,
                "res_id": res_id,
                "type": "binary",
                "mimetype": att.get("mimetype") or "application/octet-stream",
                "datas": base64.b64encode(file_content),
            }
            return self.fix(self.env["ir.attachment"].create(vals))

        for att in att_files:
            _create_ir_attachment(att, res_model, new_object.id)

    @api.model
    def get_state_id(self, data, state_id):
        if not state_id:
            return False
        row_data = data["res_country_state"].get(state_id, {})
        state_code = row_data.get("code", False)
        state = self.env["res.country.state"].search([("code", "=", state_code)], limit=1)
        return state.id if state else False

    @api.model
    def get_country_id(self, data, country_id):
        if not country_id:
            return False
        row_data = data["res_country"].get(country_id, {})
        country_code = row_data.get("code", False)
        country = self.env["res.country"].search([("code", "=", country_code)], limit=1)
        return country.id if country else False

    @api.model
    def get_country_group_id(self, data, country_group_id):
        if not country_group_id:
            return False
        row_data = data["res_country_group"].get(country_group_id, {})
        name = self.fetch_from_json(row_data.get("name", False))
        if name == "European Union":
            name = "European Union VAT"
        country_group = self.env["res.country.group"].search([("name", "=", name)], limit=1)
        if country_group:
            return country_group.id
        vals = {
            "name": name,
        }
        country_group = self.fix(self.env["res.country.group"].create(vals))
        return country_group.id

    @api.model
    def get_currency_id(self, data, currency_id):
        if not currency_id:
            return False
        row_data = data["res_currency"].get(currency_id, {})
        currency_name = row_data.get("name", False)
        currency = self.env["res.currency"].search([("name", "=", currency_name)], limit=1)
        return currency.id if currency else False

    @api.model
    def get_partner_id(self, data, old_partner_id):
        if not old_partner_id:
            return False
        row_data = data["res_partner"].get(old_partner_id, {})
        old_parent_id = row_data.get("parent_id", False)
        parent_id = self.get_partner_id(data, old_parent_id)
        new_partner = self.env["res.partner"].search([
            ("name", "=", row_data.get("name", False)),
            ("parent_id", "=", parent_id),
        ], limit=1)
        if not new_partner:
            vals = {
                "name": row_data.get("name", False),
                "parent_id": parent_id,
                "ref": row_data.get("id", False),
                "state_id": self.get_state_id(data, row_data.get("state_id", False)),
                "country_id": self.get_country_id(data, row_data.get("country_id", False)),
                "lang": row_data.get("lang", False),
                "tz": row_data.get("tz", False),
                "vat": row_data.get("vat", False),
                "website": row_data.get("website", False),
                "function": row_data.get("function", False),
                "type": row_data.get("type", False),
                "street": row_data.get("street", False),
                "street2": row_data.get("street2", False),
                "zip": row_data.get("zip", False),
                "city": row_data.get("city", False),
                "email": row_data.get("email", False),
                "phone": row_data.get("phone", False) + ((", " + row_data.get("mobile", False)) if row_data.get("mobile", False) else ""),
                "commercial_company_name": row_data.get("commercial_company_name", False),
                "comment": row_data.get("comment", False),
                "is_company": row_data.get("is_company", False),
                "partner_share": row_data.get("partner_share", False),
                "email_normalized": row_data.get("email_normalized", False),
                "calendar_last_notif_ack": row_data.get("calendar_last_notif_ack", False)[:19] if row_data.get("calendar_last_notif_ack", False) else False,
                "phone_sanitized": row_data.get("phone_sanitized", False),
                "supplier_rank": row_data.get("supplier_rank", False),
                "customer_rank": row_data.get("customer_rank", False),
                "peppol_eas": row_data.get("peppol_eas", False),
                "google_resource": row_data.get("google_resource", False),
                "google_etag": row_data.get("google_etag", False),
                "first_name": row_data.get("first_name", False),
                "last_name": row_data.get("last_name", False),
                "birthday": row_data.get("birthday", False),
                "telegram_chat_id": row_data.get("telegram_chat_id", False),
            }
            new_partner = self.fix(self.env["res.partner"].create(vals))
            self.copy_attachments(data, "res.partner", row_data.get("id", False), new_partner)
        return new_partner.id

    @api.model
    def fetch_from_json(self, json_data, extra_key=None):
        if not json_data:
            return False
        json_data = json.loads(json_data)
        return json_data.get("en_US", json_data.get("en_GB", json_data.get(extra_key, False)))

    @api.model
    def get_bank_id(self, data, old_bank_id):
        if not old_bank_id:
            return False
        row_data = data["res_bank"].get(old_bank_id, {})
        name = row_data.get("name", False)
        bank = self.env["res.bank"].search([
            ("name", "=", name),
        ], limit=1)
        if not bank:
            vals = {
                "state": self.get_state_id(data, row_data.get("state", False)),
                "country": self.get_country_id(data, row_data.get("country", False)),
                "name": name,
                "street": row_data.get("street", False),
                "street2": row_data.get("street2", False),
                "zip": row_data.get("zip", False),
                "city": row_data.get("city", False),
                "email": row_data.get("email", False),
                "phone": row_data.get("phone", False),
                "bic": row_data.get("bic", False),
                "active": row_data.get("active", False),
            }
            bank = self.fix(self.env["res.bank"].create(vals))
        return bank.id

    @api.model
    def get_partner_bank_id(self, data, old_partner_bank_id, company_partner_id=False):
        if not old_partner_bank_id:
            return False
        row_data = data["res_partner_bank"].get(old_partner_bank_id, {})
        partner_id = self.get_partner_id(data, row_data.get("partner_id", False)) if not company_partner_id else company_partner_id
        bank_id = self.get_bank_id(data, row_data.get("bank_id", False))
        currency_id = self.get_currency_id(data, row_data.get("currency_id", False))
        acc_number = row_data.get("acc_number", False)
        partner_bank = self.env["res.partner.bank"].search([
            ("acc_number", "=", acc_number),
            ("bank_id", "=", bank_id),
            ("partner_id", "=", partner_id),
            ("currency_id", "=", currency_id),
        ], limit=1)
        if not partner_bank and not row_data.get("active", False):
            vals = {
                "acc_number": acc_number,
                "bank_id": bank_id,
                "partner_id": partner_id,
                "currency_id": currency_id,
                "sanitized_acc_number": row_data.get("sanitized_acc_number", False),
                "acc_holder_name": row_data.get("acc_holder_name", False),
            }
            partner_bank = self.fix(self.env["res.partner.bank"].create(vals))
        return partner_bank.id

    @api.model
    def get_account_id(self, data, old_account_id):
        if not old_account_id:
            return False
        row_data = data["account_account"].get(old_account_id, {})
        name = self.fetch_from_json(row_data.get("name", False))
        code = self.fetch_from_json(row_data.get("code_store", False), '1')
        type = row_data.get("account_type", False)
        currency_id = self.get_currency_id(data, row_data.get("currency_id", False))
        account = self.env["account.account"].search([
            ("code_store", "like", code),
            ("account_type", "=", type),
            ("currency_id", "=", currency_id),
        ], limit=1)
        if not account:
            vals = {
                "name": name,
                "currency_id": currency_id,
                "code_store": code,
                "account_type": type,
                "reconcile": row_data.get("reconcile", False),
                "non_trade": row_data.get("non_trade", False),
                "note": row_data.get("note", False),
                "create_asset": row_data.get("create_asset", False),
                "multiple_assets_per_line": row_data.get("multiple_assets_per_line", False),
            }
            account = self.fix(self.env["account.account"].create(vals))
        return account.id

    @api.model
    def get_journal_id(self, data, old_journal_id):
        if not old_journal_id:
            return False
        row_data = data["account_journal"].get(old_journal_id, {})
        code = row_data.get("code", False)
        type = row_data.get("type", False)
        journal = self.env["account.journal"].search([
            ("code", "=", code),
            ("type", "=", type),
        ], limit=1)
        if not journal:
            bank_account_partner_id = self.env.company.partner_id.id if type == "bank" else False
            vals = {
                "default_account_id": self.get_account_id(data, row_data.get("default_account_id", False)),
                "suspense_account_id": self.get_account_id(data, row_data.get("suspense_account_id", False)),
                "currency_id": self.get_currency_id(data, row_data.get("currency_id", False)),
                "company_id": self.env.company.id,
                "profit_account_id": self.get_account_id(data, row_data.get("profit_account_id", False)),
                "loss_account_id": self.get_account_id(data, row_data.get("loss_account_id", False)),
                "bank_account_id": self.get_partner_bank_id(data, row_data.get("bank_account_id", False), bank_account_partner_id),
                "code": code,
                "type": type,
                "invoice_reference_type": row_data.get("invoice_reference_type", False),
                "invoice_reference_model": row_data.get("invoice_reference_model", False),
                "bank_statements_source": row_data.get("bank_statements_source", False),
                "name": self.fetch_from_json(row_data.get("name", False)),
                "renewal_contact_email": row_data.get("renewal_contact_email", False),
            }
            journal = self.fix(self.env["account.journal"].create(vals))
        return journal.id

    @api.model
    def get_statement_id(self, data, old_statement_id):
        if not old_statement_id:
            return False
        row_data = data["account_bank_statement"].get(old_statement_id, {})
        journal_id = self.get_journal_id(data, row_data.get("journal_id", False))
        company_id = self.env.company.id
        name = row_data.get("name", False)
        statement = self.env["account.bank.statement"].search([
            ("name", "=", name),
            ("journal_id", "=", journal_id),
            ("company_id", "=", company_id),
        ], limit=1)
        if statement:
            return statement.id
        vals = {
            "company_id": company_id,
            "journal_id": journal_id,
            "name": name,
            "reference": row_data.get("reference", False),
            "first_line_index": row_data.get("first_line_index", False),
            "date": row_data.get("date", False),
            "balance_start": row_data.get("balance_start", False),
            "balance_end": row_data.get("balance_end", False),
            "balance_end_real": row_data.get("balance_end_real", False),
            "is_complete": row_data.get("is_complete", False),
        }
        statement = self.fix(self.env["account.bank.statement"].create(vals))
        return statement.id

    @api.model
    def get_statement_line_id(self, data, old_statement_line_id):
        if not old_statement_line_id:
            return False
        row_data = data["account_bank_statement_line"].get(old_statement_line_id, {})
        journal_id = self.get_journal_id(data, row_data.get("journal_id", False))
        company_id = self.env.company.id
        statement_id = self.get_statement_id(data, row_data.get("statement_id", False))
        partner_id = self.get_partner_id(data, row_data.get("partner_id", False))
        currency_id = self.get_currency_id(data, row_data.get("currency_id", False))
        account_number = row_data.get("account_number", False)
        partner_name = row_data.get("partner_name", False)
        transaction_type = row_data.get("transaction_type", False)
        payment_ref = row_data.get("payment_ref", False)
        amount = row_data.get("amount", False)
        amount_currency = row_data.get("amount_currency", False)
        statement_line = self.env["account.bank.statement.line"].search([
            ("journal_id", "=", journal_id),
            ("company_id", "=", company_id),
            ("statement_id", "=", statement_id),
            ("partner_id", "=", partner_id),
            ("currency_id", "=", currency_id),
            ("account_number", "=", account_number),
            ("partner_name", "=", partner_name),
            ("transaction_type", "=", transaction_type),
            ("payment_ref", "=", payment_ref),
        ], limit=1)
        if not statement_line:
            vals = {
                "journal_id": journal_id,
                "company_id": company_id,
                "statement_id": statement_id,
                "sequence": row_data.get("sequence", False),
                "partner_id": partner_id,
                "currency_id": currency_id,
                "account_number": account_number,
                "partner_name": partner_name,
                "transaction_type": transaction_type,
                "payment_ref": payment_ref,
                "internal_index": row_data.get("internal_index", False),
                "amount": amount,
                "amount_currency": amount_currency,
                "is_reconciled": row_data.get("is_reconciled", False),
                "amount_residual": row_data.get("amount_residual", False),
                "cron_last_check": row_data.get("cron_last_check", False)[:19],
            }
            statement_line = self.fix(self.env["account.bank.statement.line"].create(vals))
        return statement_line.id

    @api.model
    def get_fiscal_position_id(self, data, old_fiscal_position_id):
        if not old_fiscal_position_id:
            return False
        row_data = data["account_fiscal_position"].get(old_fiscal_position_id, {})
        company_id = self.env.company.id
        country_id = self.get_country_id(data, row_data.get("country_id", False))
        country_group_id = self.get_country_group_id(data, row_data.get("country_group_id", False))
        name = self.fetch_from_json(row_data.get("name", False))
        fiscal_position = self.env["account.fiscal.position"].search([
            ("name", "=", name),
            ("company_id", "=", company_id),
            ("country_id", "=", country_id),
            ("country_group_id", "=", country_group_id),
        ], limit=1)
        if not fiscal_position:
            vals = {
                "name": name,
                "company_id": company_id,
                "country_id": country_id,
                "country_group_id": country_group_id,
                "vat_required": row_data.get("vat_required", False),
            }
            fiscal_position = self.fix(self.env["account.fiscal.position"].create(vals))
        return fiscal_position.id

    @api.model
    def get_tax_group_id(self, data, old_tax_group_id):
        if not old_tax_group_id:
            return False
        row_data = data["account_tax_group"].get(old_tax_group_id, {})
        name = self.fetch_from_json(row_data.get("name", False))
        tax_group = self.env["account.tax.group"].search([("name", "=", name)], limit=1)
        if not tax_group:
            vals = {
                "company_id": self.env.company.id,
                "tax_payable_account_id": self.get_account_id(data, row_data.get("tax_payable_account_id", False)),
                "tax_receivable_account_id": self.get_account_id(data, row_data.get("tax_receivable_account_id", False)),
                "advance_tax_payment_account_id": self.get_account_id(data, row_data.get("advance_tax_payment_account_id", False)),
                "country_id": self.get_country_id(data, row_data.get("country_id", False)),
                "name": name,
            }
            tax_group = self.fix(self.env["account.tax.group"].create(vals))
        return tax_group.id

    @api.model
    def get_tax_line_id(self, data, old_tax_line_id):
        if not old_tax_line_id:
            return False
        row_data = data["account_tax"].get(old_tax_line_id, {})
        amount = row_data.get("amount", False)
        type_tax_use = row_data.get("type_tax_use", False)
        tax = self.env["account.tax"].search([
            ("amount", "=", amount),
            ("type_tax_use", "=", type_tax_use)
        ], limit=1)
        if not tax:
            vals = {
                "company_id": self.env.company.id,
                "tax_group_id": self.get_tax_group_id(data, row_data.get("tax_group_id", False)),
                "country_id": self.get_country_id(data, row_data.get("country_id", False)),
                "type_tax_use": type_tax_use,
                "tax_scope": row_data.get("tax_scope", False),
                "amount_type": row_data.get("amount_type", False),
                "tax_exigibility": row_data.get("tax_exigibility", False),
                "name": self.fetch_from_json(row_data.get("name", False)),
                "description": self.fetch_from_json(row_data.get("description", False)),
                "invoice_label": self.fetch_from_json(row_data.get("invoice_label", False)),
                "amount": amount,
                "active": row_data.get("active", False),
            }
            tax = self.fix(self.env["account.tax"].create(vals))
        return tax.id

    @api.model
    def get_product_category_id(self, data, old_product_category_id):
        if not old_product_category_id:
            return False
        row_data = data["product_category"].get(old_product_category_id, {})
        name = self.fetch_from_json(row_data.get("name", False))

        goods_cat = self.env.ref("product.product_category_goods")
        expenses_cat = self.env.ref("product.product_category_expenses")
        services_cat = self.env.ref("product.product_category_services")

        parent_mapping = {
            "Health service": services_cat.id,
            "Health Devices": goods_cat.id,
            "Travel service": services_cat.id,
            "Telecom service": services_cat.id,
            "Public Utilities": services_cat.id,
            "Clothes and Shoes": goods_cat.id,
            "Software Subscription": expenses_cat.id,
            "Medicines": goods_cat.id,
            "Food": goods_cat.id,
        }

        parent_id = parent_mapping.get(name, False)
        product_category = self.env["product.category"].search([
            ("name", "=", name),
            ("parent_id", "=", parent_id)
        ], limit=1)
        if not product_category:
            vals = {
                "name": name,
                "parent_id": parent_id,
            }
            product_category = self.fix(self.env["product.category"].create(vals))
        return product_category.id

    @api.model
    def get_product_id(self, data, old_product_id):
        if not old_product_id:
            return False
        row_data = data["product_product"].get(old_product_id, {})
        template_data = data["product_template"].get(row_data.get("product_tmpl_id", False), {})
        name = self.fetch_from_json(template_data.get("name", False))
        product = self.env["product.product"].search([("name", "=", name)], limit=1)
        if not product:
            vals = {
                "categ_id": self.get_product_category_id(data, template_data.get("categ_id", False)),
                "type": template_data.get("type", False),
                "default_code": template_data.get("default_code", False),
                "name": name,
                "description": self.fetch_from_json(template_data.get("description", False)),
                "sale_ok": template_data.get("sale_ok", False),
                "purchase_ok": template_data.get("purchase_ok", False),
                "warranty_months": template_data.get("warranty_months", False),
                "warranty_start_date": template_data.get("warranty_start_date", False),
                "warranty_end_date": template_data.get("warranty_end_date", False),
            }
            product = self.fix(self.env["product.product"].create(vals))
            self.copy_attachments(data, "product.template", template_data["id"], product.product_tmpl_id)
            self.copy_attachments(data, "product.product", row_data["id"], product)
        return product.id

    @api.model
    def get_tax_ids(self, data, old_aml_id):
        if not old_aml_id:
            return False
        account_tax_ids = data["account_move_line_account_tax_rel"].get(old_aml_id, [])
        tax_ids = [self.get_tax_id(data, tax_id) for tax_id in account_tax_ids]
        return tax_ids

    @api.model
    def get_tax_id(self, data, old_tax_id):
        if not old_tax_id:
            return False
        row_data = data["account_tax"].get(old_tax_id, {})
        type_tax_use = row_data.get("type_tax_use", False)
        amount_type = row_data.get("amount_type", False)
        name = self.fetch_from_json(row_data.get("name", False))
        tax = self.env["account.tax"].search([
            ("name", "=", name),
            ("type_tax_use", "=", type_tax_use),
            ("amount_type", "=", amount_type),
        ], limit=1)
        if not tax:
            vals = {
                "company_id": self.env.company.id,
                "sequence": int(row_data.get("sequence", False)),
                "tax_group_id": self.get_tax_group_id(data, row_data.get("tax_group_id", False)),
                "country_id": self.get_country_id(data, row_data.get("country_id", False)),
                "type_tax_use": type_tax_use,
                "tax_scope": row_data.get("tax_scope", False),
                "amount_type": amount_type,
                "tax_exigibility": row_data.get("tax_exigibility", False),
                "name": name,
                "description": self.fetch_from_json(row_data.get("description", False)),
                "invoice_label": self.fetch_from_json(row_data.get("invoice_label", False)),
                "amount": float(row_data.get("amount", False)),
                "active": bool(row_data.get("active", False)),
            }
            tax = self.fix(self.env["account.tax"].create(vals))
        return tax.id

    @api.model
    def migrate_account_move_lines(self, data):
        _logger.info("[Rok Migration] Migrate account move lines: start")
        am_vals = {}
        for row_data in data["account_move_line"].values():
            if row_data.get("display_type", False) in ["tax", "payment_term"]:
                continue
            line_vals = {
                "account_id": self.get_account_id(data, row_data.get("account_id", False)),
                "partner_id": self.get_partner_id(data, row_data.get("partner_id", False)),
                "statement_line_id": self.get_statement_line_id(data, row_data.get("statement_line_id", False)),
                "statement_id": self.get_statement_id(data, row_data.get("statement_id", False)),
                "tax_line_id": self.get_tax_line_id(data, row_data.get("tax_line_id", False)),
                "tax_group_id": self.get_tax_group_id(data, row_data.get("tax_group_id", False)),
                "product_id": self.get_product_id(data, row_data.get("product_id", False)),
                "ref": row_data.get("ref", False),
                "name": row_data.get("name", False),
                "display_type": row_data.get("display_type", False),
                "date": row_data.get("date", False),
                "invoice_date": row_data.get("invoice_date", False),
                "date_maturity": row_data.get("date_maturity", False),
                "balance": row_data.get("balance", False),
                "amount_currency": row_data.get("amount_currency", False),
                "quantity": row_data.get("quantity", False),
                "price_unit": row_data.get("price_unit", False),
                "tax_ids": self.get_tax_ids(data, row_data.get("id", False)),
            }
            move_id = row_data.get("move_id", False)
            if not move_id in am_vals:
                am_vals[move_id] = self.prepare_am_vals(data, move_id)
            am_vals[move_id]["line_ids"].append(line_vals)

        for move_id, move_vals in am_vals.items():
            move_vals["line_ids"] = [Command.create(line_vals) for line_vals in move_vals["line_ids"]]
        move_vals_list = [move_vals for move_vals in am_vals.values()]

        moves = self.fix(self.env["account.move"].create(move_vals_list))
        moves.action_post()
        _logger.info("[Rok Migration] Migrate account move lines: end")

    @api.model
    def prepare_am_vals(self, data, move_id):
        row_data = data["account_move"].get(move_id, {})
        am_vals = {
                "journal_id": self.get_journal_id(data, row_data.get("journal_id", False)),
                "company_id": self.env.company.id,
                "statement_line_id": self.get_statement_line_id(data, row_data.get("statement_line_id", False)),
                "partner_id": self.get_partner_id(data, row_data.get("partner_id", False)),
                "commercial_partner_id": self.get_partner_id(data, row_data.get("commercial_partner_id", False)),
                "partner_shipping_id": self.get_partner_id(data, row_data.get("partner_shipping_id", False)),
                "partner_bank_id": self.get_partner_bank_id(data, row_data.get("partner_bank_id", False)),
                "fiscal_position_id": self.get_fiscal_position_id(data, row_data.get("fiscal_position_id", False)),
                "currency_id": self.get_currency_id(data, row_data.get("currency_id", False)),
                "ref": row_data.get("ref", False),
                "move_type": row_data.get("move_type", False),
                "payment_reference": row_data.get("payment_reference", False),
                "payment_state": row_data.get("payment_state", False),
                "invoice_partner_display_name": row_data.get("invoice_partner_display_name", False),
                "date": row_data.get("date", False),
                "invoice_date": row_data.get("invoice_date", False),
                "invoice_date_due": row_data.get("invoice_date_due", False),
                "narration": row_data.get("narration", False),
                "invoice_currency_rate": row_data.get("invoice_currency_rate", False),
                # "amount_untaxed": row_data.get("amount_untaxed", False),
                # "amount_tax": row_data.get("amount_tax", False),
                # "amount_total": row_data.get("amount_total", False),
                # "amount_residual": row_data.get("amount_residual", False),
                # "amount_untaxed_signed": row_data.get("amount_untaxed_signed", False),
                # "amount_untaxed_in_currency_signed": row_data.get("amount_untaxed_in_currency_signed", False),
                # "amount_tax_signed": row_data.get("amount_tax_signed", False),
                # "amount_total_signed": row_data.get("amount_total_signed", False),
                # "amount_total_in_currency_signed": row_data.get("amount_total_in_currency_signed", False),
                # "amount_residual_signed": row_data.get("amount_residual_signed", False),
                "always_tax_exigible": row_data.get("always_tax_exigible", False),
                "line_ids": [],
        }
        return am_vals
