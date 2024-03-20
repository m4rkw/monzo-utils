-- MariaDB dump 10.19  Distrib 10.6.12-MariaDB, for debian-linux-gnu (aarch64)
--
-- Host: localhost    Database: monzo
-- ------------------------------------------------------
-- Server version	10.6.12-MariaDB-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account`
--

DROP TABLE IF EXISTS `account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `account` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `provider_id` bigint(20) unsigned NOT NULL,
  `name` varchar(64) NOT NULL,
  `balance` decimal(8,2) NOT NULL,
  `available` decimal(8,2) NOT NULL,
  `type` varchar(64) NOT NULL,
  `sortcode` varchar(8) DEFAULT NULL,
  `account_no` varchar(8) DEFAULT NULL,
  `account_id` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `account_provider_id_foreign` (`provider_id`),
  CONSTRAINT `account_provider_id_foreign` FOREIGN KEY (`provider_id`) REFERENCES `provider` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `counterparty`
--

DROP TABLE IF EXISTS `counterparty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `counterparty` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(32) NOT NULL,
  `account_id` varchar(32) DEFAULT NULL,
  `account_number` varchar(8) DEFAULT NULL,
  `name` varchar(64) NOT NULL,
  `preferred_name` varchar(64) DEFAULT NULL,
  `beneficiary_account_type` varchar(32) DEFAULT NULL,
  `sort_code` varchar(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `merchant`
--

DROP TABLE IF EXISTS `merchant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `merchant` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `merchant_id` varchar(48) NOT NULL,
  `group_id` varchar(32) NOT NULL,
  `name` varchar(64) NOT NULL,
  `logo` varchar(255) NOT NULL,
  `category` varchar(32) NOT NULL,
  `online` tinyint(1) unsigned NOT NULL,
  `atm` tinyint(1) unsigned NOT NULL,
  `disable_feedback` tinyint(1) unsigned NOT NULL,
  `suggested_tags` varchar(64) DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `emoji` blob DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=111 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `merchant_address`
--

DROP TABLE IF EXISTS `merchant_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `merchant_address` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `merchant_id` bigint(20) unsigned NOT NULL,
  `short_formatted` varchar(255) NOT NULL,
  `city` varchar(64) NOT NULL,
  `latitude` float(10,6) NOT NULL,
  `longitude` float(10,6) NOT NULL,
  `zoom_level` tinyint(1) unsigned NOT NULL,
  `approximate` tinyint(1) unsigned NOT NULL,
  `formatted` varchar(255) NOT NULL,
  `address` varchar(255) NOT NULL,
  `region` varchar(64) NOT NULL,
  `country` varchar(8) NOT NULL,
  `postcode` varchar(16) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `merchant_address_merchant_id` (`merchant_id`),
  CONSTRAINT `merchant_address_merchant_id` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=111 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `merchant_metadata`
--

DROP TABLE IF EXISTS `merchant_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `merchant_metadata` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `merchant_id` bigint(20) unsigned NOT NULL,
  `key` varchar(64) NOT NULL,
  `value` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `merchant_metadata_id_foreign` (`merchant_id`),
  CONSTRAINT `merchant_metadata_id_foreign` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=461 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pot`
--

DROP TABLE IF EXISTS `pot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pot` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `account_id` bigint(20) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `balance` decimal(8,2) DEFAULT NULL,
  `pot_id` varchar(64) DEFAULT NULL,
  `deleted` tinyint(1) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `pot_account_id_foreign` (`account_id`),
  CONSTRAINT `pot_account_id_foreign` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `provider`
--

DROP TABLE IF EXISTS `provider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `provider` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transaction`
--

DROP TABLE IF EXISTS `transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transaction` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `account_id` bigint(20) unsigned NOT NULL,
  `date` date NOT NULL,
  `type` varchar(255) NOT NULL,
  `description` varchar(255) NOT NULL,
  `money_in` decimal(8,2) DEFAULT NULL,
  `money_out` decimal(8,2) DEFAULT NULL,
  `pending` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `currency` varchar(5) DEFAULT NULL,
  `local_currency` varchar(5) DEFAULT NULL,
  `local_amount` decimal(10,2) DEFAULT NULL,
  `notes` varchar(255) DEFAULT NULL,
  `originator` tinyint(1) DEFAULT NULL,
  `scheme` varchar(64) DEFAULT NULL,
  `settled` datetime DEFAULT NULL,
  `transaction_id` varchar(255) DEFAULT NULL,
  `merchant_id` bigint(20) DEFAULT NULL,
  `pot_id` bigint(20) unsigned DEFAULT NULL,
  `declined` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `decline_reason` varchar(255) DEFAULT NULL,
  `counterparty_id` bigint(20) unsigned DEFAULT NULL,
  `ref` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `transaction_account_id_foreign` (`account_id`),
  KEY `pot_id` (`pot_id`),
  KEY `counterparty_id` (`counterparty_id`),
  CONSTRAINT `transaction_account_id_foreign` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`),
  CONSTRAINT `transaction_ibfk_1` FOREIGN KEY (`pot_id`) REFERENCES `pot` (`id`),
  CONSTRAINT `transaction_ibfk_2` FOREIGN KEY (`counterparty_id`) REFERENCES `counterparty` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=32713 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transaction_metadata`
--

DROP TABLE IF EXISTS `transaction_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transaction_metadata` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` bigint(20) unsigned NOT NULL,
  `key` varchar(64) NOT NULL,
  `value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `metadata_transaction_id_foreign` (`transaction_id`),
  CONSTRAINT `metadata_transaction_id_foreign` FOREIGN KEY (`transaction_id`) REFERENCES `transaction` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26287 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-11-04  8:57:28
