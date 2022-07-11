# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [1.1.4](https://github.com/Kyostenas/prettyTables/compare/v1.1.3...v1.1.4) (2022-07-11)


### Bug Fixes

* Accidental import. ([47e798a](https://github.com/Kyostenas/prettyTables/commit/47e798a9019b918b47ace50d5fe5683864e5e886))
* Auto trimming fixed. ([92e3a66](https://github.com/Kyostenas/prettyTables/commit/92e3a668fb931da0225b375d03c72f2ce9e357d0))
* Auto-wrapping fixed. ([4b8d631](https://github.com/Kyostenas/prettyTables/commit/4b8d631dc9f7dbe65053e25b854dc61c7d6fbb64))
* Autwrapping with index shown fixed. ([cbcb70c](https://github.com/Kyostenas/prettyTables/commit/cbcb70c8a08c5572553a3b46cad822cc316d5025))
* Columns not showing wen passing less headers in class args. ([1559fe4](https://github.com/Kyostenas/prettyTables/commit/1559fe41f347130e44f07c67cdd464ca23f0cf68))
* Passing extra headers causes an IndexError. ([e5a3e42](https://github.com/Kyostenas/prettyTables/commit/e5a3e427cf226d6eb4e58fb658d5068be1700edd))
* Using rows and headers arguments gives error. ([0479cd5](https://github.com/Kyostenas/prettyTables/commit/0479cd569396db5a08c9b51be7816b53e0e0f8f9))

### [1.1.3](https://github.com/Kyostenas/prettyTables/compare/v1.1.2...v1.1.3) (2022-05-07)


### Bug Fixes

* more accidental imports ([25e4c88](https://github.com/Kyostenas/prettyTables/commit/25e4c88e0feab8f154547ae159d0d7d8fff0750b))

### [1.1.2](https://github.com/Kyostenas/prettyTables/compare/v1.1.1...v1.1.2) (2022-05-07)


### Bug Fixes

* accidental import. ([736ab4d](https://github.com/Kyostenas/prettyTables/commit/736ab4dc281cb766f9726512e3505a5bb17fc0cc))

### [1.1.1](https://github.com/Kyostenas/prettyTables/compare/v1.1.0...v1.1.1) (2022-05-07)


### Bug Fixes

* adding column of different size causing misplaced missing values. ([66abc50](https://github.com/Kyostenas/prettyTables/commit/66abc5082488c734ffd9329be09f9dc6ea86683b))
* unintended info printing on console. ([560af0a](https://github.com/Kyostenas/prettyTables/commit/560af0aa8016ab71ad11f9f7ce29375543c192a9))

## [1.1.0](https://github.com/Kyostenas/prettyTables/compare/v1.0.0...v1.1.0) (2022-05-07)


### Features

* added auto-wrapping for string columns. ([0cacdef](https://github.com/Kyostenas/prettyTables/commit/0cacdef34c738d0d611440ab393f474f37858ae3))
* added float parsing and alignment ([1a65acd](https://github.com/Kyostenas/prettyTables/commit/1a65acd7a3fc7deb7331de4bed20a9d276d1a87d))
* added show_index option ([8b8d328](https://github.com/Kyostenas/prettyTables/commit/8b8d328af591a7d0edd288d80af029837f300f81))
* auto-wrap depends on the auto_wrap option. ([a1e09e5](https://github.com/Kyostenas/prettyTables/commit/a1e09e50ec913343b5b48b679cf08128ba74a383))
* column data trimming added. ([f53503b](https://github.com/Kyostenas/prettyTables/commit/f53503bc0b1bf3bd342286ba5cb16354ab8ee4ab))
* show_empty_columns, show_empty_rows options ([a7e4288](https://github.com/Kyostenas/prettyTables/commit/a7e428845254d68368e9bce6a7fbb4a59fe4046f))


### Bug Fixes

* add_column omitting columns_with_i ([4cc900d](https://github.com/Kyostenas/prettyTables/commit/4cc900d25c494fbc2dcf4b58a7c7794c42d22b81))
* auto-wrapping doesn't wrap columns "equally". ([9ba68ab](https://github.com/Kyostenas/prettyTables/commit/9ba68aba7c8c7494c33682368921802bc5167436))
* empty column and row hiding working bad ([76979e9](https://github.com/Kyostenas/prettyTables/commit/76979e9b803491e6335cdcca8f7417f99abf8542))
* float columns weren't considering header size ([f8ffce3](https://github.com/Kyostenas/prettyTables/commit/f8ffce38a2b97d409ca7ba37677280d8ff329c68))
* header wrapping wasn't working ([09b5136](https://github.com/Kyostenas/prettyTables/commit/09b513653f89dc61331301c2be5b1506366d0fdc))
* hiding empty r/c when showing i behaving bad ([823776a](https://github.com/Kyostenas/prettyTables/commit/823776ae5b1ca9b9210a8cd8337847a79fd5625f))
* index displays incorrectly when hiding empty rows ([6054dda](https://github.com/Kyostenas/prettyTables/commit/6054ddae743df58907802c1467f8993d937c7df7))
* large missing val. in float col. causes bad alignment ([565d58c](https://github.com/Kyostenas/prettyTables/commit/565d58c9db550d63d634c1f49c972a7c8beb7b8f))
* missing value was a normal value and was affecting alignment ([a01d4fa](https://github.com/Kyostenas/prettyTables/commit/a01d4fa1b7dcc03f3ba78f31b9984ba7a7f4d334))
* read_json not closing json ([6702f53](https://github.com/Kyostenas/prettyTables/commit/6702f5330f11d1f2a70b811e68f9a26447a065f6))
* table with index wasn't auto-wrapping ([23457a5](https://github.com/Kyostenas/prettyTables/commit/23457a542733a40931f875db76f2a62939ffa93e))
* when displaying index and adding rows table data messes up. ([3c0a724](https://github.com/Kyostenas/prettyTables/commit/3c0a7245dd09597ac46028bf31a03d37014c0ccc))
* when showing i table data displays incomplete. ([b33ed42](https://github.com/Kyostenas/prettyTables/commit/b33ed42d064b1875e70357dedc1b2005ba396379))
* wrapping wasn't working ([cf63647](https://github.com/Kyostenas/prettyTables/commit/cf63647a741dec0867cb702d75d16c3b0301d3e1))
