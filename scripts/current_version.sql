ALTER SCHEMA `disrapid`  DEFAULT CHARACTER SET utf8mb4 ;

CREATE TABLE `schema` (
  `id` INT NOT NULL,
  PRIMARY KEY (`id`));

INSERT INTO `schema` (`id`) VALUES ('1');

CREATE TABLE `guilds` (
  `id` BIGINT(32) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `notify_channel_id` BIGINT(32) NULL,
  PRIMARY KEY (`id`));

CREATE TABLE `guilds_channels` (
  `id` BIGINT(32) NOT NULL,
  `guild_id` BIGINT(32) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `channeltype` ENUM("text", "voice", "private", "group", "category", "news", "store") NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_channels_guild_idx` (`guild_id` ASC),
  CONSTRAINT `fk_channels_guilds`
    FOREIGN KEY (`guild_id`)
    REFERENCES `guilds` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE TABLE `guilds_welcomemessage` (
  `id` BIGINT(32) NOT NULL AUTO_INCREMENT,
  `guild_id` BIGINT(32) NOT NULL,
  `text` VARCHAR(2000) NOT NULL,
  `enable` TINYINT(1) NOT NULL,
  `channel_id` BIGINT(32) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_welcomemessage_channel_id_idx` (`channel_id` ASC),
  CONSTRAINT `fk_welcomemessage_channel_id`
    FOREIGN KEY (`channel_id`)
    REFERENCES `guilds_channels` (`id`)
    ON DELETE CASCADE
    ON UPDATE RESTRICT,
  INDEX `fk_welcomemessage_guild_id_idx` (`guild_id` ASC),
    CONSTRAINT `fk_welcomemessage_guild_id`
    FOREIGN KEY (`guild_id`)
    REFERENCES `guilds` (`id`)
    ON DELETE CASCADE
    ON UPDATE RESTRICT);

CREATE TABLE `guilds_roles` (
  `id` BIGINT(32) NOT NULL,
  `guild_id` BIGINT(32) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_roles_guild_id_idx` (`guild_id` ASC),
  CONSTRAINT `fk_roles_guild_id`
    FOREIGN KEY (`guild_id`)
    REFERENCES `guilds` (`id`)
    ON DELETE CASCADE
    ON UPDATE RESTRICT);

CREATE TABLE `youtube` (
  `id` BIGINT(32) NOT NULL AUTO_INCREMENT,
  `valid` TINYINT(1) NOT NULL,
  `ytchannel_id` VARCHAR(255) NOT NULL,
  `last_seen` DATETIME NULL DEFAULT NULL,
  `last_goal` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`));

CREATE TABLE `guilds_youtubefollow` (
  `guild_id` BIGINT(32) NOT NULL,
  `youtube_id` BIGINT(32) NOT NULL,
  `monitor_videos` TINYINT(1) NOT NULL DEFAULT 0,
  `monitor_goals` TINYINT(1) NOT NULL DEFAULT 0,
  `monitor_streams` TINYINT(1) NOT NULL DEFAULT 0,
  `remind_streams` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`guild_id`, `youtube_id`),
  INDEX `fk_youtubefollow_youtube_id_idx` (`youtube_id` ASC),
  CONSTRAINT `fk_youtubefollow_guild_id`
    FOREIGN KEY (`guild_id`)
    REFERENCES `guilds` (`id`)
    ON DELETE CASCADE
    ON UPDATE RESTRICT,
  CONSTRAINT `fk_youtubefollow_youtube_id`
    FOREIGN KEY (`youtube_id`)
    REFERENCES `youtube` (`id`)
    ON DELETE CASCADE
    ON UPDATE RESTRICT);

CREATE TABLE `youtube_activities` (
  `id` VARCHAR(32) NOT NULL,
  `youtube_id` BIGINT(32) NOT NULL,
  `last_sequence` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_activities_youtube_id_idx` (`youtube_id` ASC),
  CONSTRAINT `fk_activities_youtube_id`
    FOREIGN KEY (`youtube_id`)
    REFERENCES `youtube` (`id`)
    ON DELETE CASCADE
    ON UPDATE RESTRICT);

CREATE TABLE `youtube_goals` (
  `id` INT NOT NULL,
  `min` INT NOT NULL,
  `max` INT NOT NULL,
  `image` VARCHAR(255) NULL DEFAULT NULL,
  `text` VARCHAR(2000) NOT NULL,
  PRIMARY KEY (`id`));

INSERT INTO `youtube_goals` (`id`, `min`, `max`, `text`) 
VALUES 
('0', '0', '49', 'likely nobody is here'),
('100', '100', '199', 'Congratz $channelname, has just reached 100 subscribers! Keep going!'),
('200', '200', '299', 'Congratz $channelname, has just reached 200 subscribers! Keep going!'),
('300', '300', '399', 'Congratz $channelname, has just reached 300 subscribers! Keep going!'),
('400', '400', '499', 'Congratz $channelname, has just reached 400 subscribers! Keep going!'),
('500', '500', '599', 'Congratz $channelname, has just reached 500 subscribers! Keep going!'),
('600', '600', '699', 'Congratz $channelname, has just reached 600 subscribers! Keep going!'),
('700', '700', '799', 'Congratz $channelname, has just reached 700 subscribers! Keep going!'),
('800', '800', '899', 'Congratz $channelname, has just reached 800 subscribers! Keep going!'),
('900', '900', '999', 'Congratz $channelname, has just reached 900 subscribers! Keep going!'),
('1000', '1000', '1999', 'Congratz $channelname, has just reached 1k subscribers! Keep going!'),
('2000', '2000', '2999', 'Congratz $channelname, has just reached 2k subscribers! Keep going!'),
('3000', '3000', '3999', 'Congratz $channelname, has just reached 3k subscribers! Keep going!'),
('4000', '4000', '4999', 'Congratz $channelname, has just reached 4k subscribers! Keep going!'),
('5000', '5000', '5999', 'Congratz $channelname, has just reached 5k subscribers! Keep going!'),
('6000', '6000', '6999', 'Congratz $channelname, has just reached 6k subscribers! Keep going!'),
('7000', '7000', '7999', 'Congratz $channelname, has just reached 7k subscribers! Keep going!'),
('8000', '8000', '8999', 'Congratz $channelname, has just reached 8k subscribers! Keep going!'),
('9000', '9000', '9999', 'Congratz $channelname, has just reached 9k subscribers! Keep going!'),
('10000', '10000', '19999', 'Congratz $channelname, has just reached 10k subscribers! Keep going!'),
('20000', '20000', '29999', 'Congratz $channelname, has just reached 20k subscribers! Keep going!'),
('30000', '30000', '39999', 'Congratz $channelname, has just reached 30k subscribers! Keep going!'),
('40000', '40000', '49999', 'Congratz $channelname, has just reached 40k subscribers! Keep going!'),
('50000', '50000', '59999', 'Congratz $channelname, has just reached 50k subscribers! Keep going!'),
('60000', '60000', '69999', 'Congratz $channelname, has just reached 60k subscribers! Keep going!'),
('70000', '70000', '79999', 'Congratz $channelname, has just reached 70k subscribers! Keep going!'),
('80000', '80000', '89999', 'Congratz $channelname, has just reached 80k subscribers! Keep going!'),
('90000', '90000', '99999', 'Congratz $channelname, has just reached 90k subscribers! Keep going!'),
('100000', '100000', '199999', 'Congratz $channelname, has just reached 100k subscribers! Keep going!'),
('200000', '200000', '299999', 'Congratz $channelname, has just reached 200k subscribers! Keep going!'),
('300000', '300000', '399999', 'Congratz $channelname, has just reached 300k subscribers! Keep going!'),
('400000', '400000', '499999', 'Congratz $channelname, has just reached 400k subscribers! Keep going!'),
('500000', '500000', '599999', 'Congratz $channelname, has just reached 500k subscribers! Keep going!'),
('600000', '600000', '699999', 'Congratz $channelname, has just reached 600k subscribers! Keep going!'),
('700000', '700000', '799999', 'Congratz $channelname, has just reached 700k subscribers! Keep going!'),
('800000', '800000', '899999', 'Congratz $channelname, has just reached 800k subscribers! Keep going!'),
('900000', '900000', '999999', 'Congratz $channelname, has just reached 900k subscribers! Keep going!'),
('1000000', '1000000', '1999999', 'Congratz $channelname, has just reached 1M subscribers! Keep going!'),
('2000000', '2000000', '2999999', 'Congratz $channelname, has just reached 2M subscribers! Keep going!'),
('3000000', '3000000', '3999999', 'Congratz $channelname, has just reached 3M subscribers! Keep going!'),
('4000000', '4000000', '4999999', 'Congratz $channelname, has just reached 4M subscribers! Keep going!'),
('5000000', '5000000', '5999999', 'Congratz $channelname, has just reached 5M subscribers! Keep going!'),
('6000000', '6000000', '6999999', 'Congratz $channelname, has just reached 6M subscribers! Keep going!'),
('7000000', '7000000', '7999999', 'Congratz $channelname, has just reached 7M subscribers! Keep going!'),
('8000000', '8000000', '8999999', 'Congratz $channelname, has just reached 8M subscribers! Keep going!'),
('9000000', '9000000', '9999999', 'Congratz $channelname, has just reached 9M subscribers! Keep going!'),
('10000000', '10000000', '19999999', 'Congratz $channelname, has just reached 10M subscribers! Keep going!'),
('20000000', '20000000', '29999999', 'Congratz $channelname, has just reached 20M subscribers! Keep going!'),
('30000000', '30000000', '39999999', 'Congratz $channelname, has just reached 30M subscribers! Keep going!'),
('40000000', '40000000', '49999999', 'Congratz $channelname, has just reached 40M subscribers! Keep going!'),
('50000000', '50000000', '59999999', 'Congratz $channelname, has just reached 50M subscribers! Keep going!'),
('60000000', '60000000', '69999999', 'Congratz $channelname, has just reached 60M subscribers! Keep going!'),
('70000000', '70000000', '79999999', 'Congratz $channelname, has just reached 70M subscribers! Keep going!'),
('80000000', '80000000', '89999999', 'Congratz $channelname, has just reached 80M subscribers! Keep going!'),
('90000000', '90000000', '99999999', 'Congratz $channelname, has just reached 90M subscribers! Keep going!'),
('100000000', '100000000', '199999999', 'Congratz $channelname, has just reached 100M subscribers! Did you every see that?');