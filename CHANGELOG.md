# Changelog

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
