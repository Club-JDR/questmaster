# Changelog

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
