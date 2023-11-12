PRAGMA synchronous = OFF;
PRAGMA journal_mode = MEMORY;
BEGIN TRANSACTION;
CREATE TABLE "account" (
  "id" integer primary key autoincrement NOT NULL ,
  "provider_id" bigint(20)  NOT NULL,
  "name" varchar(64) NOT NULL,
  "balance" decimal(8,2) NOT NULL,
  "available" decimal(8,2) NOT NULL,
  "type" varchar(64) NOT NULL,
  "sortcode" varchar(8) DEFAULT NULL,
  "account_no" varchar(8) DEFAULT NULL,
  "account_id" varchar(64) DEFAULT NULL,
  CONSTRAINT "account_provider_id_foreign" FOREIGN KEY ("provider_id") REFERENCES "provider" ("id")
);
CREATE TABLE "counterparty" (
  "id" integer primary key autoincrement NOT NULL ,
  "user_id" varchar(32) NOT NULL,
  "account_id" varchar(32) DEFAULT NULL,
  "account_number" varchar(8) DEFAULT NULL,
  "name" varchar(64) NOT NULL,
  "preferred_name" varchar(64) DEFAULT NULL,
  "beneficiary_account_type" varchar(32) DEFAULT NULL,
  "sort_code" varchar(6) DEFAULT NULL
);
CREATE TABLE "merchant" (
  "id" integer primary key autoincrement NOT NULL ,
  "merchant_id" varchar(48) NOT NULL,
  "group_id" varchar(32) NOT NULL,
  "name" varchar(64) NOT NULL,
  "logo" varchar(255) NOT NULL,
  "category" varchar(32) NOT NULL,
  "online" tinyint(1)  NOT NULL,
  "atm" tinyint(1)  NOT NULL,
  "disable_feedback" tinyint(1)  NOT NULL,
  "suggested_tags" varchar(64) DEFAULT NULL,
  "website" varchar(255) DEFAULT NULL,
  "emoji" blob
);
CREATE TABLE "merchant_address" (
  "id" integer primary key autoincrement NOT NULL ,
  "merchant_id" bigint(20)  NOT NULL,
  "short_formatted" varchar(255) NOT NULL,
  "city" varchar(64) NOT NULL,
  "latitude" float(10,6) NOT NULL,
  "longitude" float(10,6) NOT NULL,
  "zoom_level" tinyint(1)  NOT NULL,
  "approximate" tinyint(1)  NOT NULL,
  "formatted" varchar(255) NOT NULL,
  "address" varchar(255) NOT NULL,
  "region" varchar(64) NOT NULL,
  "country" varchar(8) NOT NULL,
  "postcode" varchar(16) NOT NULL,
  CONSTRAINT "merchant_address_merchant_id" FOREIGN KEY ("merchant_id") REFERENCES "merchant" ("id")
);
CREATE TABLE "merchant_metadata" (
  "id" integer primary key autoincrement NOT NULL ,
  "merchant_id" bigint(20)  NOT NULL,
  "key" varchar(64) NOT NULL,
  "value" varchar(255) NOT NULL,
  CONSTRAINT "merchant_metadata_id_foreign" FOREIGN KEY ("merchant_id") REFERENCES "merchant" ("id")
);
CREATE TABLE "pot" (
  "id" integer primary key autoincrement NOT NULL ,
  "account_id" bigint(20)  NOT NULL,
  "name" varchar(255) NOT NULL,
  "balance" decimal(8,2) DEFAULT NULL,
  "pot_id" varchar(64) DEFAULT NULL,
  "deleted" tinyint(1)  NOT NULL DEFAULT '0',
  CONSTRAINT "pot_account_id_foreign" FOREIGN KEY ("account_id") REFERENCES "account" ("id")
);
CREATE TABLE "provider" (
  "id" integer primary key autoincrement NOT NULL ,
  "name" varchar(64) NOT NULL
);
CREATE TABLE "transaction" (
  "id" integer primary key autoincrement NOT NULL ,
  "account_id" bigint(20)  NOT NULL,
  "date" date NOT NULL,
  "type" varchar(255) NOT NULL,
  "description" varchar(255) NOT NULL,
  "money_in" decimal(8,2) DEFAULT NULL,
  "money_out" decimal(8,2) DEFAULT NULL,
  "pending" tinyint(1)  NOT NULL DEFAULT '0',
  "created_at" datetime NOT NULL,
  "updated_at" datetime NOT NULL,
  "currency" varchar(5) DEFAULT NULL,
  "local_currency" varchar(5) DEFAULT NULL,
  "local_amount" decimal(8,2) DEFAULT NULL,
  "notes" varchar(255) DEFAULT NULL,
  "originator" tinyint(1) DEFAULT NULL,
  "scheme" varchar(64) DEFAULT NULL,
  "settled" datetime DEFAULT NULL,
  "transaction_id" varchar(255) DEFAULT NULL,
  "merchant_id" bigint(20) DEFAULT NULL,
  "pot_id" bigint(20)  DEFAULT NULL,
  "declined" tinyint(1)  NOT NULL DEFAULT '0',
  "decline_reason" varchar(255) DEFAULT NULL,
  "counterparty_id" bigint(20)  DEFAULT NULL,
  "ref" varchar(255) DEFAULT NULL,
  CONSTRAINT "transaction_account_id_foreign" FOREIGN KEY ("account_id") REFERENCES "account" ("id"),
  CONSTRAINT "transaction_ibfk_1" FOREIGN KEY ("pot_id") REFERENCES "pot" ("id"),
  CONSTRAINT "transaction_ibfk_2" FOREIGN KEY ("counterparty_id") REFERENCES "counterparty" ("id")
);
CREATE TABLE "transaction_metadata" (
  "id" integer primary key autoincrement NOT NULL ,
  "transaction_id" bigint(20)  NOT NULL,
  "key" varchar(64) NOT NULL,
  "value" varchar(255) DEFAULT NULL,
  CONSTRAINT "metadata_transaction_id_foreign" FOREIGN KEY ("transaction_id") REFERENCES "transaction" ("id")
);
CREATE INDEX "merchant_metadata_merchant_metadata_id_foreign" ON "merchant_metadata" ("merchant_id");
CREATE INDEX "transaction_metadata_metadata_transaction_id_foreign" ON "transaction_metadata" ("transaction_id");
CREATE INDEX "transaction_transaction_account_id_foreign" ON "transaction" ("account_id");
CREATE INDEX "transaction_pot_id" ON "transaction" ("pot_id");
CREATE INDEX "transaction_counterparty_id" ON "transaction" ("counterparty_id");
CREATE INDEX "account_account_provider_id_foreign" ON "account" ("provider_id");
CREATE INDEX "pot_pot_account_id_foreign" ON "pot" ("account_id");
CREATE INDEX "merchant_address_merchant_address_merchant_id" ON "merchant_address" ("merchant_id");
END TRANSACTION;
