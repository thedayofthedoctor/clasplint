## PEP 2606 — CLASP Stage 3.1 (Code Logging Annotation Standard Proposal)

### 一、变量名标准化全部要求

第一：变量名格式必须为 `group1_group2`，有且仅有一个下划线。组内可由多个单词直接拼接而成，组内不再有额外下划线。
第二：变量名全部使用小写字母，禁止任何形式的大写字母。专有缩写（如 `gps`、`utm`、`xmp`、`gdal`、`xml`、`epsg` 等）在变量名中也必须转为全小写。
第三：变量名中出现的单词必须完整拼写，禁止任何形式的缩写。允许的例外仅限于领域内以全大写缩写形式存在的专有名词（如 `gps`、`utm`、`xmp`、`gdal`、`epsg`、`xml`），这些专有名词在变量名中转为全小写后仍可使用。普通英语单词如 `directory`、`index`、`sequence`、`coefficient`、`multiplier` 等必须写全，不得缩写为 `dir`、`idx`、`seq`、`coeff`、`mul` 等。
第四：类型前缀（如 `list_`、`dict_`、`string_`、`bool_`、`int_`、`float_` 等）允许使用，且必须位于变量名的开头位置，即 `类型前缀_内容描述` 格式。例如 `list_utmzones`、`dict_defaultmeta`。
第五：布尔值变量使用 `is_` 或 `has_` 作为前缀，整体仍为一个下划线。例如 `has_distortion`、`is_valid`。
第六：表示集合的变量名中，组内单词可以使用复数形式。如 `list_utmzones` 中的 `utmzones` 是允许的，整个变量名仍只含一个下划线。
第七：常量变量同样使用全小写蛇形命名，且必须符合两段式格式（一个下划线）。禁止使用全大写命名常量。例如 `nodata_value`、`default_focal`。
第八：变量名总长度不得超过 30 个字符。若超过，需在不违反完整拼写原则的前提下压缩组内单词数量或调整表达方式。
第九：所有变量名均须按照上述规则进行标准化。仅当变量用于与外部系统直接交互（如调用第三方库时必须使用的特定参数名），且标准化后会导致交互失败等不可用情况时，才允许保持原样，不进行标准化。

### 二、字典键名标准化全部要求

第一：字典键名采用驼峰式命名，首字母大写，后续每个单词首字母大写。例如 `FilePath`、`BandName`、`GPSLongitude`。
第二：字典键名中的单词必须完整拼写，禁止任何缩写。例如 `DistortionCoefficients` 不得写为 `DistortionCoeffs`，`TileMultiplier` 不得写为 `TileMul`。
第三：专有缩写（如 `GPS`、`UTM`、`UTC`、`GSD`、`RGB`、`NIR`、`XML`、`XMP`、`EPSG`、`CRS` 等）在字典键名中保持全大写。例如 `GPSLatitude`、`UTMZone`、`UTCAtExposure`。
第四：嵌套字典的内部键名同样遵循上述驼峰、完整拼写、专有缩写大写的规则。例如 `band_config` 中的内部键应改为 `Pattern`、`HighRes`、`TileMultiplier`。
第五：动态生成的字典键名，必须依照其来源字段按照本标准进行标准化转换。即若来源字段在标准化后为驼峰式，则字典键名也应为对应的驼峰式。
第六：若字典用于与外部系统直接交互（如 `xml_namespaces` 的键名必须与 XML 结构中的实际名称保持一致），且标准化后会导致交互失败等不可用情况，则允许保持原样，不进行标准化。除此类不可抗力外，所有字典键名均须标准化。

### 三、函数命名标准化全部要求

第一：类名命名采用大驼峰式（PascalCase），每个单词首字母大写，且不使用下划线。例如 `CameraModel`、`ImageProcessor`、`MetadataExtractor`。

第二：函数名采用蛇形命名（snake_case），全部小写，单词之间用下划线分隔。例如 `calculate_gsd`、`extract_metadata`、`generate_tiles`。

第三：函数名中的单词必须完整拼写，禁止任何形式的缩写。例如 `calculate_gsd` 中的 `calculate` 不得写为 `calc`，`generate_tiles` 中的 `generate` 不得写为 `gen`。

第四：专有缩写（如 `gps`、`utm`、`xmp`、`gdal`、`xml`、`epsg` 等）在函数名中也必须转为全小写。例如 `calculate_gps_coordinates` 中的 `gps` 是允许的。

第五：函数名总长度不得超过 30 个字符。若超过，需在不违反完整拼写原则的前提下压缩单词数量或调整表达方式。

第六：函数名应清晰表达函数的核心功能和作用，避免使用模糊或过于宽泛的词汇，如 `process`、`handle`、`manage` 等。应优先使用具体的动词来描述函数的行为，例如 `calculate`、`extract`、`generate`、`validate` 等。

第七：所有函数名均须按照上述规则进行标准化。仅当函数用于与外部系统直接交互（如调用第三方库时必须使用的特定函数名），且标准化后会导致交互失败等不可用情况时，才允许保持原样，不进行标准化。

第八：类公共方法同样遵循函数命名的标准化规则，命名要简短，方法名开头结尾不得出现 `_`。例如 `CameraModel` 类中的方法应命名为 `run`、`start` 等，而非 `CalculateGSD` 或 `_run_name_`。

第九：类私有方法，命名要细致，并且命名格式为 `_init_` + 描述名（2~8 个单词，总字符数不超过 30）+ `_function_`。例如 `CameraModel` 类中的私有方法可以命名为 `_init_calculate_gsd_function_`、`_init_extract_metadata_function_` 等。

### 四、代码行注释和日志消息标准化全部要求

第一：所有物理行，包括但不限于 `try`、`except`、`if`、`else`、`elif`、`return`、`raise`、`continue`、`pass` 等控制流语句和操作语句，以及普通赋值语句、函数调用语句，必须逐条、逐行、逐个进行分段式注释。注释格式固定为 `#` 后接一个空格，再接一个首字母大写的完整英文句子，描述紧随其后的那一行代码的核心意图或逻辑，句子末尾必须加句号。以下结构性声明行可豁免注释要求：`import` 语句、`from ... import ...` 语句、`class` 定义行、`def` / `async def` 定义行。

第二：注释必须清晰、无歧义，直接对应下一行代码的功能。对于条件判断和异常捕获等关键节点，注释应明确说明条件为真或异常发生时的预期行为，禁止使用 `Check if ...` 这样仅复述代码而不揭示意图的写法。

第三：所有涉及外部资源交互、数据读写、网络请求或用户输入输出的操作，必须根据需求构建完整的 `try-except` 问题捕获与传递链条。每一层异常处理都必须输出日志，形成可追溯的错误信息流。

第四：日志消息（如有）必须提前定义为字符串变量，严禁将日志文本直接内联在日志函数的括号参数内。日志变量命名须符合本规范“变量名标准化”的 `group1_group2` 全小写规则，例如 `message_error_empty_api`。随后再将该变量传递给日志方法。

第五：每条日志（如有）消息应包含足够上下文，如当前操作的关键变量值或失败的目标资源。记录异常时必须显式设置 `exc_info=True` 以输出完整堆栈。

第六：日志（如有）级别必须按语义严格区分：调试信息使用 `debug`，常规流程使用 `info`，可恢复异常使用 `warning`，不可恢复错误使用 `error`，严重系统级故障使用 `critical`。不得在所有场景中滥用同一级别。

第七：在 `try-except` 链条中，如果某一层只记录日志（如有）并继续向上传递异常，必须使用 `raise` 保留原始异常上下文，并在日志（如有）中说明向上传递的原因。如果在某一层终结异常，则必须用注释说明终结逻辑和后续补偿措施。

第八：对于 `if`、`elif`、`else` 分支，每个分支内第一条可执行语句前必须放置注释，说明进入该分支的条件以及该分支将要执行的操作。循环结构的第一行可执行语句前也须用注释概括迭代对象和终止条件。

第九：整个代码库中注释与日志（如有）消息必须使用统一语言。注释整体采用英文，日志（如有）整体采用中文。日志（如有）消息中允许谨慎使用表情符号以增强可读性，但必须保证日志（如有）解析系统不受干扰。

第十：不得以任何形式在代码中使用非标准化的注释或日志（如有）消息。所有注释和日志必须严格遵守上述规范，确保代码的可读性、可维护性和可追溯性。

### 五、文档字符串标准化全部要求

第一：每个 Python 文件必须包含文件级文档字符串（file docstring），位于文件最顶部（shebang 和编码声明之后）。文件文档字符串格式如下：

- 第一行：`THIS FILE IS PART OF <项目名> BY <作者名>`，全部大写。
- 第二行：`<模块路径> — <一句话功能描述>`。
- 紧接着：`Author:` 作者名、`Create Date:` 创建日期、`Version Date:` 版本日期、`Version:` 版本号。
- 紧接着：`THIS PROGRAM IS LICENSED UNDER <许可证标识>`，全部大写，后跟 `YOU SHOULD HAVE RECEIVED A COPY OF <许可证标识> LICENSE.`。
- 紧接着：`Copyright (C) <年份> <作者名>`。
- 紧接着：完整的许可证条款文本（如 GPL-3.0 标准条款）。

第二：每个类必须包含类级文档字符串（class docstring）描述类的核心职责。格式为一句话简要描述，空行后列出公开方法和私有方法及其一句话功能说明：

```
Brief one-line description of what this class does.

Public methods:
    method_name — Brief description of what the method does.

Private methods:
    _init_method_function_ — Brief description of what the private method does.
```

第三：每个函数和方法必须包含文档字符串。模块级函数和类的文档字符串仅需存在性检查。类方法（包括 `__init__`）的文档字符串必须遵循 Sphinx 指令格式：

- 使用多行 `"""..."""` 格式，`"""` 独占首尾行。
- 第一段为一句简要概述。
- 空行后为详细逻辑描述段落（1~3 句），解释该方法的具体实现逻辑和行为。
- 空行后为指令段，依次列出：

  - `:param <参数名>: <描述>` — 每个参数（不含 `self`、`cls`）必须有。
  - `:type <参数名>: <类型>` — 每个参数（不含 `self`、`cls`）必须有。
  - `:return: <描述>` — 当方法有非 `None` 返回类型注解时必须存在。
  - `:rtype: <类型>` — 对应 `:return` 必须存在。

第四：文档字符串中的描述文本必须使用完整拼写、首字母大写的英文句子，以句号结尾。禁止使用 Markdown 或其他标记语法。

第五：仅当方法与外部系统直接交互（如 Python `ast.NodeVisitor` 的 `visit_*` 回调方法）且标准化后会导致交互失败时，才允许豁免文档字符串格式要求。方法必须存在于明确继承 `ast.NodeVisitor` 的类中方能享受此豁免。