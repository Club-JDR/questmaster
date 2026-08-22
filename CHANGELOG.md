# Changelog

## [1.8.0](https://github.com/Club-JDR/questmaster/compare/v1.7.1...v1.8.0) (2026-08-22)


### Features

* **admin:** add cache-clearing CLI command and admin settings panel ([d199cee](https://github.com/Club-JDR/questmaster/commit/d199cee6d98fee41cdf7523d5b53bd65c02fe069))
* **admin:** let a superuser admin view-as another user ([e8f1757](https://github.com/Club-JDR/questmaster/commit/e8f175748aaf346bc188a5cbe9ecd16266d34603))
* **admin:** let an admin manually award or revoke trophies for an archived game ([b983480](https://github.com/Club-JDR/questmaster/commit/b9834806c25509b03b0b6feffa7fa34c026de028))
* **badges:** add per-event leaderboard tab to the badge classement page ([f9f4662](https://github.com/Club-JDR/questmaster/commit/f9f4662d559e23587a10d7ef51876c3ab5373319))
* **ci:** skip lint and tests when only docs, templates or workflows change ([71e13b3](https://github.com/Club-JDR/questmaster/commit/71e13b3d20b5404b09655276c716faba70165de8))
* **discord:** /avertir and /infractions moderation slash commands ([d97e8c7](https://github.com/Club-JDR/questmaster/commit/d97e8c7f0bdca9f77bf62e3df7db29e2f2de0010))
* **discord:** sidekick bot to run QuestMaster actions via slash commands ([0cdaea3](https://github.com/Club-JDR/questmaster/commit/0cdaea3be69b20c8bda747d3395dfbea00e909a6))
* **games:** add a placeholder for additional info in the game form ([8c13c9d](https://github.com/Club-JDR/questmaster/commit/8c13c9d864d8bbff0883ff7766968f45fae740d5))
* **games:** add open-to-viewers flag with spectator follow + agenda ([9334ec7](https://github.com/Club-JDR/questmaster/commit/9334ec7fb99ff73ab016944217547191b66bdc10))
* **games:** allow switching a published game between one-shot and campaign ([d090817](https://github.com/Club-JDR/questmaster/commit/d0908176cc80f9f56f9d78e73754742ba9f330a4))
* **games:** block self-registration on a schedule conflict ([baf15fb](https://github.com/Club-JDR/questmaster/commit/baf15fbfa2938b4711ddd256822f9ca5df5bc4b0))
* **games:** let a GM branch a campaign into a quick replacement one-shot ([81cff83](https://github.com/Club-JDR/questmaster/commit/81cff8364ccb658c1783fcf91bb9933c0ba6543b))
* **games:** per-user defaults for the game creation form ([7e53aa9](https://github.com/Club-JDR/questmaster/commit/7e53aa9a292a05dae248abed94a539aa5a120b99))
* **games:** persist whether trophies were awarded on archive ([dfe55f4](https://github.com/Club-JDR/questmaster/commit/dfe55f45663d0976a8b1c279b6769f59c395ed78))
* **games:** render description/complement as sanitized Markdown ([1599a4f](https://github.com/Club-JDR/questmaster/commit/1599a4fb0e6c570b19b608208bfd4631a701b20d))
* **moderation:** in-app infractions to replace Mee6 !warn / !infractions ([39fdcf5](https://github.com/Club-JDR/questmaster/commit/39fdcf56b47540d7674f5f0573d31cbe1df267fc))
* **systems:** add public system pages with lightweight matchmaking ([84c66e0](https://github.com/Club-JDR/questmaster/commit/84c66e08550ee80356c1cf4e6847abd619185aa2))
* **users:** let admins block a GM from posting games ([1af7c93](https://github.com/Club-JDR/questmaster/commit/1af7c93a523b71ece9331e0b3e623fbe882b9b6c))


### Bug Fixes

* **admin:** move discord_message.sent_at to a DB-side default ([b79c058](https://github.com/Club-JDR/questmaster/commit/b79c05881fb6e8fac492a1a0da7581759654d269))
* **admin:** prevent game-event action badges from wrapping and overflowing ([dc7f8d3](https://github.com/Club-JDR/questmaster/commit/dc7f8d34111bab4e72a4980431ee1f52256e8c05))
* **api:** make the health endpoint reflect actual DB/cache connectivity ([b3791df](https://github.com/Club-JDR/questmaster/commit/b3791dfd213a8fb48ebee2aa5f4e65312645ffa5))
* **auth:** harden session cookie flags (secure + samesite) ([50afc76](https://github.com/Club-JDR/questmaster/commit/50afc76ac84b8ad14429a92e650b6052734ef65c))
* **auth:** stop looping deleted-but-logged-in users into repeated 404s ([8ce1b49](https://github.com/Club-JDR/questmaster/commit/8ce1b49ee89537aa3cee0214cbccbfeb1e79f43d))
* **ci:** stop release job being skipped via transitive changes-job dependency ([c926001](https://github.com/Club-JDR/questmaster/commit/c926001da3075ac6822922c1ba5ec42562876bbd))
* **ci:** tolerate slow Postgres first boot in compose healthchecks ([4cdd3af](https://github.com/Club-JDR/questmaster/commit/4cdd3afa4b5bab596377768f71461686b68c7798))
* **config:** fail fast when required env vars are missing ([a53b9d3](https://github.com/Club-JDR/questmaster/commit/a53b9d3f0a862ea48d176e956df18c90a2ea6e75))
* **db:** set pool_pre_ping and pool_recycle on the SQLAlchemy engine ([3a8cfbc](https://github.com/Club-JDR/questmaster/commit/3a8cfbc99b3c22af72c455e951d2fcf1f126aae1))
* **demo:** stop baking demo game dates in at import time ([a2dd41f](https://github.com/Club-JDR/questmaster/commit/a2dd41f876d69a6111d04b73849f93074463cafd))
* **deps:** update dependency marshmallow to v4.3.1 ([902f3f4](https://github.com/Club-JDR/questmaster/commit/902f3f4ac4e95e43604941b9c892f4bc3d24bcf8))
* **deps:** update dependency nh3 to v0.3.6 ([45da806](https://github.com/Club-JDR/questmaster/commit/45da806cda6b48f5920dc2d2f9a13a5dec186121))
* **deps:** update dependency python-dotenv to v1.2.3 ([9734e9e](https://github.com/Club-JDR/questmaster/commit/9734e9e8748baa826a92793ff448efd69de1d388))
* **deps:** update dependency redis to v8.1.0 ([427830c](https://github.com/Club-JDR/questmaster/commit/427830ca48b1298edaeaa101be951ffe18e2e280))
* **discord:** add timeouts to all outbound Discord/CDN calls ([7af5919](https://github.com/Club-JDR/questmaster/commit/7af59192aaa5afda748d66534637b0136b37744e))
* **discord:** cap the 429 retry sleep and make get_role() raise on miss ([dc0e9ac](https://github.com/Club-JDR/questmaster/commit/dc0e9ac4c1f6a957301fbb1e7c50a561d35ccd91))
* **discord:** give rate-limit retries their own budget, separate from real attempts ([a275582](https://github.com/Club-JDR/questmaster/commit/a275582a0b5e38ceadd009a2e7f58d7fd222084c))
* event leaderboard color for players top 10 ([470d21d](https://github.com/Club-JDR/questmaster/commit/470d21d5784f37b83407f4942f8e1b22cd9d9dc4))
* **games:** address category-size drift and error-handling review findings ([9965312](https://github.com/Club-JDR/questmaster/commit/996531288eae753f168822cbf9e22c2d1b239410))
* **games:** allow managing registrations on open games without race ([9aac205](https://github.com/Club-JDR/questmaster/commit/9aac205bcf5d2edd1894a8bd601151c960502dd5))
* **games:** cap Discord notify message length ([6e6dbcb](https://github.com/Club-JDR/questmaster/commit/6e6dbcb1cf61b700c9b560bf1ccb05cc7157c4ae))
* **games:** cap request body size and validate the game img URL ([b70b913](https://github.com/Club-JDR/questmaster/commit/b70b9131b47ab3d1f7175f41b069a0046720db91))
* **games:** close gaps in the schedule-conflict check ([9a86e98](https://github.com/Club-JDR/questmaster/commit/9a86e989ee5a7f7a02d04b7aa3ca728c1eb3713e))
* **games:** convert _get_game_if_participant to raise instead of returning a Response ([f5ff6d6](https://github.com/Club-JDR/questmaster/commit/f5ff6d69ee7b9776a67d7aaa0fa85e49d9bcd42b))
* **games:** correct blueprint prefix in special-event search pagination ([c227a97](https://github.com/Club-JDR/questmaster/commit/c227a97b45bd8519b50a504b4339bca51e77b688))
* **games:** don't lie about trophies_awarded when awarding fails ([a39e2d9](https://github.com/Club-JDR/questmaster/commit/a39e2d9b9d52be973331d1832d71a548a928d289))
* **games:** guard against Discord role/channel names over 100 chars ([29c3bbe](https://github.com/Club-JDR/questmaster/commit/29c3bbec35667e30a5fa42e06e6f7a02fb8002be))
* **games:** guard session-date parsing and action lookup against malformed input ([e91c439](https://github.com/Club-JDR/questmaster/commit/e91c439ee1bd9cb1b45789fab6c7e045cf3f866a))
* **games:** migrate Game.date and GameSession.start/end to aware UTC ([72d5bc1](https://github.com/Club-JDR/questmaster/commit/72d5bc1aabcacd70a15ee0b92e44efe114963713))
* **games:** never award trophies for a draft game ([7440060](https://github.com/Club-JDR/questmaster/commit/7440060bfb0712115c2c6ef871ca447066ce3d12))
* **games:** raise instead of redirect on unauthorized game access ([a6e42a0](https://github.com/Club-JDR/questmaster/commit/a6e42a0f5ac13d17c7efb639f26c4dcd02fc69c7))
* **games:** raise NotFoundError from get_filtered_user_games on missing user ([1284632](https://github.com/Club-JDR/questmaster/commit/1284632e9a8bc9833e3dbe2d73d2dcc6ac76229f))
* **games:** stop trusting gm_id from the creation form ([9d2241e](https://github.com/Club-JDR/questmaster/commit/9d2241ed97ba875dbde3107b187c80a756adf8fd))
* **games:** validate session belongs to game before edit/delete ([1bb81b9](https://github.com/Club-JDR/questmaster/commit/1bb81b95a3af678b931f4125057f2c0d013caa36))
* **ops:** cap the DB pool and recycle gunicorn workers for small prod host ([82db29c](https://github.com/Club-JDR/questmaster/commit/82db29cd379055bbc94b8e8ffcae2c15cbf12a16))
* **scheduler:** run APScheduler in one dedicated compose service ([62b4eb2](https://github.com/Club-JDR/questmaster/commit/62b4eb2fd2d43402ee53117727838ac82c9740a0))
* **security:** autoescape .j2 templates to prevent stored XSS ([9cd641e](https://github.com/Club-JDR/questmaster/commit/9cd641ecf44a82735124df12575b8f99aa1d64b9))
* **tests:** make current-month stats test resist shared-DB pollution ([7a6343a](https://github.com/Club-JDR/questmaster/commit/7a6343a530b9113684bb8f3024d90e3beba81355))
* **tests:** reset the special_event id sequence past its reserved fixture id ([8035a71](https://github.com/Club-JDR/questmaster/commit/8035a71c3706385c4031d3e1ab8085650d9821d6))
* timezone, error-handling, and duplication issues from code review ([f865b13](https://github.com/Club-JDR/questmaster/commit/f865b13e8028a9f2b8705f256784da43adecd2a1))


### Performance Improvements

* **discord:** reuse a pooled requests.Session in the Discord client ([fd96d3e](https://github.com/Club-JDR/questmaster/commit/fd96d3e917d6cc14522289633c18d4104cc76cd7))
* **logging:** move DB/webhook log writes off the request thread ([e4fa8cf](https://github.com/Club-JDR/questmaster/commit/e4fa8cff5155c3a22f749af84385379d7628d3df))

## [1.7.1](https://github.com/Club-JDR/questmaster/compare/v1.7.0...v1.7.1) (2026-07-14)


### Bug Fixes

* **admin/logs:** collapse stacktrace rows behind a detail modal ([b042ce9](https://github.com/Club-JDR/questmaster/commit/b042ce97ecafbcd5881a2b3ea0504f7bbe413f8d))
* **deps:** update dependency flask-caching to v2.4.1 ([87b0a08](https://github.com/Club-JDR/questmaster/commit/87b0a081bd6346ff17f13521a487a4b1b5487df2))
* **embeds:** show "Consulter" button on closed game announcements ([7dbdd64](https://github.com/Club-JDR/questmaster/commit/7dbdd64cf90fa7529835b8c0d900dab6e1d44d18))
* **games:** cap slug length so Discord role/channel names fit the 100-char limit ([509f634](https://github.com/Club-JDR/questmaster/commit/509f63411d16bfab1b472637330bfe6fffbf06fc))
* **games:** don't re-run setup or delete channel on re-publish in direct mode ([af58d46](https://github.com/Club-JDR/questmaster/commit/af58d46f420802069c7cece74d40050f14044be4))
* **games:** guard draft publishing against past dates and draft sessions ([a0dcb09](https://github.com/Club-JDR/questmaster/commit/a0dcb095e71cf1272facd46c7e3c6eae8f8d5e40))
* **scheduler:** lower profile-refresh batch size and make it configurable ([495eb6b](https://github.com/Club-JDR/questmaster/commit/495eb6b6a8f31300a15f03de148ca82e581d1d1e))
* **stats:** correct play-time inflation and miscounts ([4acfc31](https://github.com/Club-JDR/questmaster/commit/4acfc3160cdba58fa73e75991165d950163f4870))


### Documentation

* refresh documentation to match current status ([50b5aca](https://github.com/Club-JDR/questmaster/commit/50b5acaf4d5d4906d0adbd989f0516ad5cb2fc98))

## [1.7.0](https://github.com/Club-JDR/questmaster/compare/v1.6.0...v1.7.0) (2026-07-03)


### Features

* **admin:** add granular permissions (RBAC) for delegated admin access ([c799d3a](https://github.com/Club-JDR/questmaster/commit/c799d3a2c8bc6bf386bdc714bc8695660f88a3b5))
* **channels:** reconcile, create, and auto-provision Discord categories ([fe27c60](https://github.com/Club-JDR/questmaster/commit/fe27c6060d5da5c43bc0299473bc9ea696d0c5ce))
* **dashboard:** agenda-first personalised landing dashboard ([24af753](https://github.com/Club-JDR/questmaster/commit/24af753149dc911410c19a051e3ed83e223adf38))
* **discord:** add direct channel permissions mode and GM notify button ([579bbdf](https://github.com/Club-JDR/questmaster/commit/579bbdfec7647fdf07855189e0d76ef0fd735744))
* **discord:** multi-embed messages with link buttons ([8bfb3f7](https://github.com/Club-JDR/questmaster/commit/8bfb3f7194f3cae1815883af23f6b27bbcfac9cf))
* **games:** normalise imgur page URLs to direct image links on the game form ([444976c](https://github.com/Club-JDR/questmaster/commit/444976ca5f311ee16ca65409cbcaedf0ca72dcc8))
* **logging:** persist app logs with admin browsing page ([#188](https://github.com/Club-JDR/questmaster/issues/188)) ([2ec706d](https://github.com/Club-JDR/questmaster/commit/2ec706da3712a38d178db1b5b87f402785a46464))
* **settings:** make card-grid page size admin-configurable ([0da1eaa](https://github.com/Club-JDR/questmaster/commit/0da1eaab13e13db94e6d7ebefd8198108a718cc0))
* **stats:** app-wide overview on the statistics page ([f6ab7a0](https://github.com/Club-JDR/questmaster/commit/f6ab7a00dc3fcec57edeb8485d7ab64c476908f4))
* **users:** add and search users by Discord username ([c11fb22](https://github.com/Club-JDR/questmaster/commit/c11fb224857356d90e1b4ca84df2e0ef6c07ca81))


### Bug Fixes

* **deps:** update dependency apscheduler to v3.11.3 ([#182](https://github.com/Club-JDR/questmaster/issues/182)) ([53d639d](https://github.com/Club-JDR/questmaster/commit/53d639d34b3b7ce436759307bcf505ccb4b1be78))
* **deps:** update dependency pydoclint to v0.9.1 ([#177](https://github.com/Club-JDR/questmaster/issues/177)) ([22113ff](https://github.com/Club-JDR/questmaster/commit/22113ff97185cdd94004f0f83e556417bec7c42e))
* **deps:** update dependency redis to v8.0.1 ([#179](https://github.com/Club-JDR/questmaster/issues/179)) ([f38dcdf](https://github.com/Club-JDR/questmaster/commit/f38dcdfcdbc8dce18f350c146dfd64a88c866963))
* **scheduler:** persist refreshed Discord profiles so admin shows real names ([09a4003](https://github.com/Club-JDR/questmaster/commit/09a40037d32319a96c220e72883d84e1fc157685))


### Documentation

* document RBAC, dashboard, and Discord category auto-provisioning ([fe7278c](https://github.com/Club-JDR/questmaster/commit/fe7278c1f6a4b5581c9ff25b9d0760673f244d79))

## [1.6.0](https://github.com/Club-JDR/questmaster/compare/v1.5.1...v1.6.0) (2026-06-20)


### Features

* **a11y:** WCAG 2.2 AA pass over the public UI ([9cc2615](https://github.com/Club-JDR/questmaster/commit/9cc2615f68382322fb739a838a0c793a2142da05))
* **admin:** add one-click trophy increment/decrement ([ce54c34](https://github.com/Club-JDR/questmaster/commit/ce54c3499b9ea12cdd5a92feffeb991e1732691e))
* **admin:** add search and pagination to admin list views ([01ba5b9](https://github.com/Club-JDR/questmaster/commit/01ba5b94f70be858b5d2670fe2b864c141ce220b))
* **admin:** link GM name in games list to user games page ([ec64858](https://github.com/Club-JDR/questmaster/commit/ec6485827e62026a1fd28d43e3218b7f83579778))
* **admin:** list games for a specific special event ([d2b7877](https://github.com/Club-JDR/questmaster/commit/d2b7877e4bb526cb8d647c4e5911075ea41e9327))
* **admin:** list games per user (as GM and as player) ([efe457f](https://github.com/Club-JDR/questmaster/commit/efe457fc3dcb33064ca876f3636bef7a3fe36838))
* **admin:** manage messages and channels in admin ([8b58285](https://github.com/Club-JDR/questmaster/commit/8b58285edee56c728c4bd01ad9b5d8dfea486a28))
* **admin:** manage user trophies from the user page ([5c19a4e](https://github.com/Club-JDR/questmaster/commit/5c19a4e29e67c7c3116ae9135493956ef2b77219))
* **admin:** replace Flask-Admin with custom DaisyUI admin blueprint ([bbdb981](https://github.com/Club-JDR/questmaster/commit/bbdb981d774e1120e651a9b70b1421830b4b9ff3))
* **api:** add game CRUD endpoints with Marshmallow validation ([b02a36e](https://github.com/Club-JDR/questmaster/commit/b02a36e35b77a2e694913b9c51331a35bce5a10f))
* **config:** allow DB overrides for operational Discord settings ([af56068](https://github.com/Club-JDR/questmaster/commit/af560687c7addcbb3042ffc1ee764aa1e627e725))
* **ui:** add image URL validation with error feedback in game form ([3ba7542](https://github.com/Club-JDR/questmaster/commit/3ba75425ba70bd583cb08630620b110ab4af93ef))
* **ui:** display sessions in reverse chronological order on game details page ([91fd9cb](https://github.com/Club-JDR/questmaster/commit/91fd9cb15eaefd359a37180725ef6d7c4ca24dbf))
* **ui:** show next upcoming session date on game card, falling back to most recent past or game date ([f7c187f](https://github.com/Club-JDR/questmaster/commit/f7c187f0d6d7cfcde2acc83244afd7eebc234605))


### Bug Fixes

* **demo:** use ISO-string dates in fake games to match serialized shape ([7e8ef70](https://github.com/Club-JDR/questmaster/commit/7e8ef70ef8622b7ca7963aafa5aeae5e06cab33c))
* **deps:** update dependency beautifulsoup4 to v4.15.0 ([6ae044f](https://github.com/Club-JDR/questmaster/commit/6ae044f36715fe1318ea79b82b99d22100a17ddd))
* **deps:** update dependency marshmallow to v4.3.0 ([#174](https://github.com/Club-JDR/questmaster/issues/174)) ([1f2cebf](https://github.com/Club-JDR/questmaster/commit/1f2cebfe4f3027e78653d6cd76a139ebe089b473))
* **deps:** update dependency pydoclint to v0.8.6 ([#142](https://github.com/Club-JDR/questmaster/issues/142)) ([879deec](https://github.com/Club-JDR/questmaster/commit/879deec2f0f62a1e634aa26bda11204266f02cbf))
* **deps:** update dependency pytest to v9.1.1 ([fc40af7](https://github.com/Club-JDR/questmaster/commit/fc40af7d8ea36787d02ba871b571c32497b470ca))
* **deps:** update dependency theme-change to v3 ([#168](https://github.com/Club-JDR/questmaster/issues/168)) ([b9f4bef](https://github.com/Club-JDR/questmaster/commit/b9f4befeb3a68cdce16b56a0e8e794f5a5bfc5fd))
* **sonar:** sanitize logged trophy names and associate form inputs with labels ([#176](https://github.com/Club-JDR/questmaster/issues/176)) ([794d69f](https://github.com/Club-JDR/questmaster/commit/794d69f0b7a89c489312f6d6283f559b6a4371f4))
* **templates:** return datetime from now() global so session sort works ([7e8ef70](https://github.com/Club-JDR/questmaster/commit/7e8ef70ef8622b7ca7963aafa5aeae5e06cab33c))

## [1.5.1](https://github.com/Club-JDR/questmaster/compare/v1.5.0...v1.5.1) (2026-05-30)


### Bug Fixes

* **game:** improve game_event log messages for status transitions ([627e8ff](https://github.com/Club-JDR/questmaster/commit/627e8ff8fe8da01439f1e3330b27da2b3b6e2fba))
* **game:** prevent double trophy award on duplicate archive requests ([f6e3f7c](https://github.com/Club-JDR/questmaster/commit/f6e3f7c80d1b826a2b951aff9251d9eaaf804653))

## [1.5.0](https://github.com/Club-JDR/questmaster/compare/v1.4.1...v1.5.0) (2026-05-29)


### Features

* **mobile:** carousel dots and swipe hint on cards pages ([be56e5e](https://github.com/Club-JDR/questmaster/commit/be56e5ec72612ce705de101b8b1426f6bb27e07c))
* **mobile:** swipe carousel for game cards ([29fd148](https://github.com/Club-JDR/questmaster/commit/29fd1485e9845ac3a86cf676ce1a435666e88dd9))
* **ui:** show latest session date on game card when more recent than game date ([26b8b2d](https://github.com/Club-JDR/questmaster/commit/26b8b2dbb0d4fe19cd1ac68f249523622f4722c8))
* **ui:** smooth card refresh with skeleton loading state ([5a6b92e](https://github.com/Club-JDR/questmaster/commit/5a6b92ef6bb9aa82ccd90cce8443e84053a109c5))
* **ui:** smooth fade transition on game card refresh ([dcacdc1](https://github.com/Club-JDR/questmaster/commit/dcacdc1dc939b455d77424348af4eb405b130310))
* **ui:** type-based card border color + status ribbon for non-open games ([bb284ec](https://github.com/Club-JDR/questmaster/commit/bb284ec8b40e5ebe0e01547f0a8119ac15a5ae27))


### Bug Fixes

* **deps:** update dependency redis to v8 ([0df3979](https://github.com/Club-JDR/questmaster/commit/0df3979cf2e94e4b52f99d6bbfc40e96656529b7))
* **templates:** compute per-session duration via duration_hours filter, handles serialized ISO strings ([3caf371](https://github.com/Club-JDR/questmaster/commit/3caf3719f57e77bf82a2a3dec9792198f9aac1d1))
* **tests:** use /annonces/cards/ endpoint for card-content assertions ([d15f86f](https://github.com/Club-JDR/questmaster/commit/d15f86f1f288a6ef579775e9fe85b585046fd753))
* **theme:** fix FOUC with inline script, wire theme-change to toggle for persistence ([9ae113f](https://github.com/Club-JDR/questmaster/commit/9ae113f9c7ee336941acef9d5e4ee686b5dcdd70))
* **theme:** respect OS dark mode preference when no theme is stored in localStorage ([52289b6](https://github.com/Club-JDR/questmaster/commit/52289b61910a9aa99a3f5c6a12db55434f94fc0a))
* **ui:** hardcode navbar color to be consistent across themes ([3bf4dfa](https://github.com/Club-JDR/questmaster/commit/3bf4dfa081496b04dcd590efe842393660ee0e71))
* **ui:** improve game card title legibility ([64d5ae2](https://github.com/Club-JDR/questmaster/commit/64d5ae26b0d8d1302d648d13e8fe3b9bef76ad53))
* **ui:** make draft/save button always visible with btn-outline ([6da9bf2](https://github.com/Club-JDR/questmaster/commit/6da9bf2005e4fdc35644200c546b4902a1af1994))

## [1.4.1](https://github.com/Club-JDR/questmaster/compare/v1.4.0...v1.4.1) (2026-05-27)


### Bug Fixes

* **css:** match DaisyUI 5.5 :is() specificity in theme overrides ([48dd9cd](https://github.com/Club-JDR/questmaster/commit/48dd9cd24ea1e48370a518d04b29cfaefe4f8e1c))
* increase ambience icon size ([51c0ebf](https://github.com/Club-JDR/questmaster/commit/51c0ebfa87a9279a0a289be6601f6741b844d789))
* **stats:** stabilize cache key for monthly stats ([2c8a6d5](https://github.com/Club-JDR/questmaster/commit/2c8a6d5e316e98875de650a4811fb41f0f2f7069))
* **templates:** replace details/summary with daisyui collapse to prevent dropdown handler interference ([4158d07](https://github.com/Club-JDR/questmaster/commit/4158d071e2fb8d1aae2ee86ff196090fec982115))
* **templates:** show "joueur·euse" label for register/unregister events instead of "par" ([7e41316](https://github.com/Club-JDR/questmaster/commit/7e41316496b08b057045bdcde946b99f2dec2936))

## [1.4.0](https://github.com/Club-JDR/questmaster/compare/v1.3.0...v1.4.0) (2026-05-27)


### Features

* **add-session:** Pre-fill add-session modal based on game frequency, fall back to game date if future, else today at game hour ([c67ab69](https://github.com/Club-JDR/questmaster/commit/c67ab693eeb7bd406985c016e6ac60e8132990db))
* **api:** add foundation + read-only endpoints ([cf47afb](https://github.com/Club-JDR/questmaster/commit/cf47afb5eab77392f45ee1bb592f4b8e14b1daef))
* **api:** session-cookie auth fallback + browser API client + /users/me/games endpoints ([da9c56b](https://github.com/Club-JDR/questmaster/commit/da9c56bf72e1c9e803265f60fbf4d5eb55f554d9))
* bundle FullCalendar via npm instead of CDN ([0e57b23](https://github.com/Club-JDR/questmaster/commit/0e57b2368406a8222931e81b48b13acd1977fbd9))
* **game-details:** add session count warnings in archive modal ([c5dc7aa](https://github.com/Club-JDR/questmaster/commit/c5dc7aa0c6064ad44db9c7eab2a8ce3626a96892))
* **game-details:** add session nudge for GMs on in-progress campaigns ([90709bf](https://github.com/Club-JDR/questmaster/commit/90709bf0a2ec089af4cab81b0ca6da5bbebe180e))
* **game-form:** pre-fill date to today 20:30 ([5a4c6cd](https://github.com/Club-JDR/questmaster/commit/5a4c6cd98b8ce39043ba7d352e8cd842aca63473))
* migration from bootstrap to daisyui ([6261a21](https://github.com/Club-JDR/questmaster/commit/6261a2156f89c7b393254cd82911aeec75c11acb))
* remove calendar intermediate modal, open picker directly on button click ([a9f1e89](https://github.com/Club-JDR/questmaster/commit/a9f1e89d02f919c2887d0c263979408877e9ad57))
* update introjs to new daisyui ([42ef826](https://github.com/Club-JDR/questmaster/commit/42ef826f3f83ef7ecc1225a35f591b41e8656b92))


### Bug Fixes

* add explicit HTTP methods to demo routes ([4b9fcbf](https://github.com/Club-JDR/questmaster/commit/4b9fcbf4dadf1340c888472e1ad670b27267309a))
* address Sonar findings in routes, pip installs, and api auth ([80185af](https://github.com/Club-JDR/questmaster/commit/80185afdc2c7f05a2e4aaa048be660c1fffa1a7e))
* adress Sonar findings in fullcalendar code ([a17f8fa](https://github.com/Club-JDR/questmaster/commit/a17f8faf8cd819fc70da384316aa94a178dda59c))
* **ci:** copy built frontend assets before running tests ([9fad823](https://github.com/Club-JDR/questmaster/commit/9fad823571fc4fc7e9e76e2498b6e1212ba21e0d))
* **ci:** fix python version in black and set sonar host url ([45d930d](https://github.com/Club-JDR/questmaster/commit/45d930de04a764b2ea902f3dc8655a55f85d8a9b))
* **ci:** use tar pipe to avoid 555-permission error when extracting dist assets ([a9e18c9](https://github.com/Club-JDR/questmaster/commit/a9e18c998f4de4554a4042235de1bc6139e8c209))
* **client:** replace unused loop variable with _ ([3e88ae4](https://github.com/Club-JDR/questmaster/commit/3e88ae48b7bedee3c73fda134cb695deb11c749f))
* **demo:** show nav buttons on all steps and fix dropdown timing on click ([a0298d2](https://github.com/Club-JDR/questmaster/commit/a0298d283aa17c770ec75ce5fc5d07c00fb336df))
* **deps:** add missing requests dependency required by Authlib flask client ([75ac4f7](https://github.com/Club-JDR/questmaster/commit/75ac4f7e1b27f0d57493267406d72cc0add78e83))
* **deps:** update dependency isort to v8 ([24a074b](https://github.com/Club-JDR/questmaster/commit/24a074b32ecddfcc8a3f2f7bc5adcbd54ada48c5))
* **deps:** update dependency python-dotenv to v1.2.2 ([6e62d00](https://github.com/Club-JDR/questmaster/commit/6e62d009a65bf3005f9c7d1b8cebc8186ed4f4f2))
* **deps:** update dependency werkzeug to v3.1.8 ([83e4bb0](https://github.com/Club-JDR/questmaster/commit/83e4bb0855f4a47e2941d56611132fa8d2c103e8))
* **docker:** add --no-emit-project to app-test uv export ([7a69ab7](https://github.com/Club-JDR/questmaster/commit/7a69ab7142799a5e4f6aab16d77634d9f468c92f))
* **docker:** copy templates into frontend builder for Tailwind class scanning ([4181e64](https://github.com/Club-JDR/questmaster/commit/4181e640ea9fb3bb5fe6458e1af1608a1e3914e5))
* **docker:** set TZ env var to resolve tzlocal warning in container ([e7502cc](https://github.com/Club-JDR/questmaster/commit/e7502cc10cac7cd1e2fb3f9524ac9169120f4b7c))
* **game:** regenerate slug when renaming a draft game ([b8fcdf3](https://github.com/Club-JDR/questmaster/commit/b8fcdf3b4eb8567be4bf6d698a2ee0c19e153c75))
* **sessions:** use human-readable datetime format in session notifications ([b1512bf](https://github.com/Club-JDR/questmaster/commit/b1512bf357fba053934dc588f1059b9cc9b622eb))
* **templates:** fallback to placeholder on broken game image URLs ([ce8d994](https://github.com/Club-JDR/questmaster/commit/ce8d99477610886d268b06a0f671afc39c50cf6d))
* **tests:** align session date assertions with data-* attribute format ([c074cf9](https://github.com/Club-JDR/questmaster/commit/c074cf9de4591bb2fa971a446c5faa816676761f))
* **tests:** align test expectations with DaisyUI template and model changes ([5673047](https://github.com/Club-JDR/questmaster/commit/567304771e5ef27e160b9061599e8c1774890152))
* **ui:** accessibility, perf and consistency improvements ([3e0d9ea](https://github.com/Club-JDR/questmaster/commit/3e0d9ea692c43b7d9f0e3886d259a43a25c16008))

## [1.3.0](https://github.com/Club-JDR/questmaster/compare/1.2.0...v1.3.0) (2026-02-18)


### Features

* add stable Discord username for slug generation ([b1262e9](https://github.com/Club-JDR/questmaster/commit/b1262e9503ed3ba2c71183d41ffd5694497cab4c))
* add user attribution to game events ([da0452f](https://github.com/Club-JDR/questmaster/commit/da0452f54c7022bc58a427d130d5e38850616baa))
* pin gm instructions msg in game channel ([2517301](https://github.com/Club-JDR/questmaster/commit/2517301083fbf4a42bfa6de88c15e49e65fb5df7))
* skip departed Discord users in scheduled profile refresh ([38b7558](https://github.com/Club-JDR/questmaster/commit/38b7558cf9cb425513f09522e770116d2caec467))


### Bug Fixes

* **deps:** update dependency flask to v3 ([aea6eae](https://github.com/Club-JDR/questmaster/commit/aea6eae44e8e1739018654a2cecbe997fd6f8682))
* **deps:** update dependency gunicorn to v25.1.0 ([bbe98b8](https://github.com/Club-JDR/questmaster/commit/bbe98b8cf73aff9a6dc413719bd73ca561b13de0))
* **deps:** update dependency isort to v7 ([241f71a](https://github.com/Club-JDR/questmaster/commit/241f71ab83245575b9a3e33eea132c5be873de2d))
* **deps:** update dependency psutil to v7 ([b1198ac](https://github.com/Club-JDR/questmaster/commit/b1198acd6145801c8486c82f3fc0f669876cc3ca))
* **deps:** update dependency pytest-cov to v7 ([6a4ae52](https://github.com/Club-JDR/questmaster/commit/6a4ae52e95f277d575d202848d506cabfddd7408))
* **deps:** update dependency tenacity to v9 ([0a22571](https://github.com/Club-JDR/questmaster/commit/0a2257131310a24fd12b387ade33d833c9ecd8f8))
* **deps:** upgrade to flask-admin 2.0.2 ([198ec08](https://github.com/Club-JDR/questmaster/commit/198ec0853de8b5093b9161f2fba604e312a1fa51))
* handle version correctly in /health/ ([2a80a2f](https://github.com/Club-JDR/questmaster/commit/2a80a2f3460e187093bd8b5a078e62805205e8f3))
* prevent data URI images from breaking Discord embeds ([db76b8b](https://github.com/Club-JDR/questmaster/commit/db76b8be26b76fa019964d82be82607ffcc25fce))
* remove gm name from calendar event ([b15c699](https://github.com/Club-JDR/questmaster/commit/b15c6991ce4472c61e63d33787128df55c99bdb2))
* **scheduler:** query user IDs before loading ORM objects to avoid init_on_load storm ([690fc07](https://github.com/Club-JDR/questmaster/commit/690fc07969a4ab8b056f48d37e57de640c318a4f))
* user trophies page should require login ([a0a012d](https://github.com/Club-JDR/questmaster/commit/a0a012d003424d063fa093bdc40494550d9e2745))


### Documentation

* add docs section and mkdocs to serve it ([03e5cbb](https://github.com/Club-JDR/questmaster/commit/03e5cbbc9de3997f3071637203bac2b16b2ec7aa))

## [1.2.0](https://github.com/Club-JDR/questmaster/compare/1.1.0...v1.2.0) (2026-02-12)


### Features

* Improve embeds ([ab922bb](https://github.com/Club-JDR/questmaster/commit/ab922bbdfe69eefdf80f03d02550cd4716d90bda))
* restructure and improve exceptions ([dcbafc5](https://github.com/Club-JDR/questmaster/commit/dcbafc52f7ffe22432e99b586396b75f905e2f18))
* restructure models and add serialization ([45fbc8a](https://github.com/Club-JDR/questmaster/commit/45fbc8a9e4c6c9c3e52ea937baaac28cf6c8e5d1))


### Bug Fixes

* **deps:** update dependency flake8 to v7.3.0 ([4cc0f5f](https://github.com/Club-JDR/questmaster/commit/4cc0f5fc9975e29fec8c2b7c0877573ee53380ab))
* **deps:** update dependency pytest to v9 ([7f15d5b](https://github.com/Club-JDR/questmaster/commit/7f15d5b68b14ea6f3b434bf3b3b7fde12c34d94e))
* lint migrations/env.py ([4e20ebd](https://github.com/Club-JDR/questmaster/commit/4e20ebd77df9306d1019bd40e31a71f2d36d8d80))
* session removal success message when failing ([ee5fc6e](https://github.com/Club-JDR/questmaster/commit/ee5fc6ee8ec5450f664a8717756290be55788019))
* set sonar Python version to 3.13 ([9c205bb](https://github.com/Club-JDR/questmaster/commit/9c205bbf1881adc01e423a3d344cd944d2579838))


### Documentation

* rewrite README ([39b2084](https://github.com/Club-JDR/questmaster/commit/39b208413e8a450ee51d4a40dbe36553c0071f81))
* update README ([fbbde6c](https://github.com/Club-JDR/questmaster/commit/fbbde6cb938791f01036568b6de1e8326a7faf20))
