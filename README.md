# asm

* Новиков Егор Сергеевич, P33101
* `asm | cisc | neum | hw | instr | struct | stream | mem | pstr | prob1 | [4]char`
* Без усложнения

## Язык программирования

Форма Бэкуса-Наура:

```text
<program> ::= [ <data_section> ] <text_section>

<data_section> ::= "section .data" <constants>
<constants> ::= <constant> | <constant> <constants>
<constant> ::= <label> ":" <const_val>
<const_val> ::= <string>

<text_section> ::= "section .text" <code_lines>
<code_lines> ::= <code_line> | <code_line> <code_lines>
<code_line> ::= <label> ":" | <local_label> ":" | <instruction>
<instruction> ::= <opcode> [ <arguments> ]
<arguments> ::= <argument> | <argument> "," <arguments>
<argument> ::= <label> | <local_label> | <memory_address> | <register> | <number> | <register_number_operation>
<memory_address> ::= "*" <register> | "*" <number>
<register_number_operation> ::= <register> <operation> <number>

<opcode> ::= "mov" | "movnum2reg" | "movnum2mem" | "movreg2reg" | "movreg2mem" | "movmem2reg" 
  | "movmem2mem" | "movregnum2reg" | "inc" | "dec" | "add" | "addreg" | "sub" | "div" | "mod" 
  | "cmp" | "push" | "pop" | "je" | "jne" | "jmp" | "call" | "ret" | "halt"

<operation> ::= "+" | "-" | "/" | "%"
<register> ::= "a0" | "a1" | "a2" | "a3" | "r0" | "r1" | "r2" | "r3" | "sp"

<number> ::= [ "-" ] <unsigned_number>
<unsigned_number> ::= <digit> | <digit> <unsigned_number>
<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<string> ::= '"' <string_letters> '"'
<string_letters> ::= "" | <string_letter> | <string_letter> <string_letters>
<string_letter> ::= <any symbol except: '"'>

<local_label> ::= "." <label>
<label> ::= <label_letters>
<label_letters> ::= <label_letter> | <label_letter> <label_letters>
<label_letter> ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" 
  | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" 
  | "V" | "W" | "X" | "Y" | "Z" | "a" | "b" | "c" | "d" | "e" | "f" | "g" 
  | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" 
  | "t" | "u" | "v" | "w" | "x" | "y" | "z" | "_"
```

Программа состоит из обязательной программной секции (начинается с `section .text`) и необязательной секции данных
(начинается с `setion .data`).

Секция с данными представляет перечисление констант, которые состоят из названия и хранящихся данных 
(`hello: "Hello, world!"`).

Программная секция состоит из последовательных инструкций (`add r1, 15`) и меток (`print:`) для логической 
группировки инструкций.

Инструкции выполняются последовательно сверху вниз, начиная с метки `start:`. 

Любая инструкция состоит из названия и аргументов. Инструкции `call` и `ret` позволяют
работать с группой инструкций, как с функцией. Инструкции условного и безусловного перехода (`jmp`, `je`, `jne`)
позволяют изменить последовательной порядок исполнения и продолжить программу с другой точки (метки).

В качестве аргумента может быть число (`42`), регистр (`r1`), операция между регистром и числом (`r0 / 10`), 
название метки или константы (`label` или `.label`), адрес памяти (`*r2` или `*100`).

Список всех инструкций и их описание можно найти в разделе "Система команд".

Метки и константы доступны из любой точки программы. Локальные метки (начинаются с точки) доступны только изнутри
функции (разные функции могут иметь одинаковые локальные метки).


## Организация памяти

Программисту доступны следующие регистры:
* `a0`, `a1`, `a2`, `a3` - регистры, обычно использующиеся для передачи аргументов
* `r0`, `r1`, `r2`, `r3` - регистры, не имеющие специального назначения
* `sp` - указатель стека, обычно использующийся для выделения памяти на стеке или передачи дополнительных аргументов

Память общая для данных и для инструкций.

Имеет примерно следующий вид:

```text
    +------------------------+
    |         Memory         |
    +------------------------+
    | 0:   jmp s             |
    | 1:   <func1 code>      |
    | ...                    |
    | f:   <func2 code>      |
    | ...                    |
    | s:   <start code>      |
    | ...                    |
    | m:   halt              |
    | m+1: empty word        |
    | m+2: <const1>          |
    | ...                    |
    | m+c: <constC>          |
    | ...                    |
    | ...                    |
    | n:   stack start       |
    +------------------------+
```

Машинное слово - 32 бита.

Первая инструкция - переход к основной программе (начинается с метки `start:`). Далее располагаются инструкции 
в том же порядке, в каком они были написаны программистом.

**Примечание**: приведен пример расположения в памяти "типичной программы". Ничего не мешает программисту расположить
основную программу в начале файла. В таком случае инструкции `jmp` не будет, память начнется сразу же с инструкций
основной программы.

За последней инструкцией исходного кода программы располагается пустое машинное слово (сделано с целью 
избежания исполнения данных, как кода).

Далее хранятся константы в том порядке, в котором они были объявлены в секции с данными.

В конце памяти находится стек, который по мере исполнения программы "растет" вверх.

Для хранения динамических данных программист может воспользоваться выделением памяти на стеке (регистр `sp`).


## Система команд

Все регистры имеют разрядность 32 бита за исключением регистра `fl`, имеющего разрядность 4 бита.

Полный список регистров:

| Название | Доступен программисту | Описание                                                |
|----------|-----------------------|---------------------------------------------------------|
| `a0`     | да                    | регистр для передачи первого аргумента функции          |
| `a1`     | да                    | регистр для передачи второго аргумента функции          |
| `a2`     | да                    | регистр для передачи третьего аргумента функции         |
| `a3`     | да                    | регистр для передачи четвертого аргумента функции       |
| `r0`     | да                    | не имеет специального назначения                        |
| `r1`     | да                    | не имеет специального назначения                        |
| `r2`     | да                    | не имеет специального назначения                        |
| `r3`     | да                    | не имеет специального назначения                        |
| `sp`     | да                    | указатель на вершину стека                              |
| `ip`     | нет                   | указатель на исполняемую инструкции                     |
| `ir`     | нет                   | содержит исполняемую инструкцию                         |
| `ar`     | нет                   | регистр адреса, используется для операций чтения/записи |
| `dr`     | нет                   | регистр данных, используется для операций чтения/записи |
| `fl`     | нет                   | содержит флаги по результатам операции (NZVC)           |

Доступ к памяти осуществляет при помощи регистров `ar` и `dr`. Для чтения необходимо задать адрес ячейки. 
Для записи необходимо задать адрес и данные.

Ввод/вывод отображается на память. Для вывода необходимо выполнить запись в ячейку памяти по определенному адресу. 
Для ввода необходимо выполнить чтение определенной (другой) ячейки памяти.

Имеется адресация памяти 2 типов:
* абсолютная (`*100`)
* абсолютная от регистра (`*r2`)

Набор инструкций:

| Инструкция                      | Описание                                                                        |
|---------------------------------|---------------------------------------------------------------------------------|
| `halt`                          | останов                                                                         |
| `call <label>`                  | вызвать функцию по ее метке (адрес возврата положить на стек)                   |
| `ret`                           | возвращение из функции (адрес возврата снять со стека)                          |
| `jmp <label>`                   | безусловный переход по адресу                                                   |
| `je <label>`                    | переход по адресу если равно (Z == 1)                                           |
| `jne <label>`                   | переход по адресу если не равно (Z == 0)                                        |
| `push <reg>`                    | положить значение регистра на стек                                              |
| `pop <reg>`                     | снять значение со стека и записать в регистр                                    |
| `cmp <reg>, <num>`              | установить флаги по результату операции вычитания числа из регистра             |
| `inc <reg>`                     | инкремент значения регистра                                                     |
| `dec <reg>`                     | декремент значения регистра                                                     |
| `add <reg>, <num>`              | прибавить к регистру число                                                      |
| `addreg <reg>, <reg>`           | прибавить к регистру значение другого регистра                                  |
| `sub <reg>, <num>`              | вычесть из регистра число                                                       |
| `div <reg>, <num>`              | поделить регистр на число (целочисленное деление)                               |
| `mod <reg>, <num>`              | деление по модулю регистра и числа                                              |
| `movnum2reg <reg>, <num/label>` | записать число в регистр                                                        |
| `movnum2mem <mem>, <num/label>` | записать число в память                                                         |
| `movreg2reg <reg>, <reg>`       | записать значение регистра в другой регистр                                     |
| `movreg2mem <mem>, <reg>`       | записать значение регистра в память                                             |
| `movmem2reg <reg>, <mem>`       | записать значение из памяти в регистр                                           |
| `movmem2mem <mem>, <mem>`       | записать значение из памяти в другую ячейку памяти (без затрагивания регистров) |
| `movregnum2reg <reg>, <regnum>` | записать результат операции регистра и числа в регистр                          |

где:
* `<label>` - метка инструкции или константы
* `<reg>` - регистр
* `<num>` - число
* `<mem>` - адрес ячейки памяти (может быть задан числом `*444` или регистром `*r4`)
* `<regnum>` - операция между регистром и числом
* `<num/label>` - можно использовать любой аргумент

**Примечание**: в исходном коде можно найти инструкцию `mov`, которая не представлена в таблице. В момент трансляции 
эта инструкция заменится на соответствующую в зависимости от предоставленных ей аргументов. То же самое для 
инструкции `add`. Однако, программист может не пользоваться этим механизмом и использовать инструкции с полным 
названием (`movreg2mem <mem>, <reg>` вместо `mov <mem>, <reg>`).

Поток управления:
* вызов `call` или возврат `ret` из функции
* условные `je`, `jne` и безусловные `jmp` переходы
* инкремент `ip` после любой другой инструкции

Машинный код сериализуется в список JSON объектов.

Пример:

```json
[
  {
    "tag": "OPCODE",
    "op": "jmp"
  },
  {
    "tag": "ARGUMENT",
    "arg": {
      "tag": "NUMBER",
      "symbol": "start",
      "val": 0
    }
  },
  {
    "tag": "BINARY",
    "val": 14
  }
]
```

где:
* `tag` - метка машинного слова, определяющая тип того, что находится в ячейке памяти (`OPCODE` - код операции, 
  `ARGUMENT` - аргумент инструкции, `BINARY` - число)
* `op` - инструкция (при `tag` равном `OPCODE`)
* `arg` - структура описания аргумента инструкции (при `tag` равном `ARGUMENT`):
  * `tag` - метка аргумента, определяющая тип аргумента (`NUMBER` - число, `REGISTER` - регистр, `ADDRESS_EXACT` - 
    адрес памяти, заданный числом, `ADDRESS_REGISTER` - адрес памяти, заданный регистром, `OPERATION` - 
    математическая операция)
  * `symbol` - метка аргумента из исходного кода (при `tag` равном `NUMBER`)
  * `val` - число (при `tag` равном `NUMBER` или `ADDRESS_EXACT`)
  * `reg` - регистр (при `tag` равном `REGISTER` или `ADDRESS_REGISTER`)
  * `op` - операция (при `tag` равном `OPERATION`)
* `val` - число, хранящееся в ячейке (при `tag` равном `BINARY`)

Одна инструкция занимает от 1 до 5 машинных слов. Меткой `BINARY` описываются константы из секции с данными.

"Типичное" расположение типов машинных слов: 
`OPCODE` - `ARGUMENT` - `OPCODE` - `ARGUMENT` - `ARGUMENT` - ... - `BINARY` - `BINARY` - ... - `BINARY`

Типы данных в модуле [isa](isa.py):
  * `Reg` - перечисление регистров
  * `ArgType` - перечисление типов аргументов инструкций
  * `Arg` - структура для описания одного аргумента инструкции
  * `Opcode` - перечисление кодов операций
  * `Term` - структура для описания одной инструкции
  * `WordTag` - перечисление типов машинного слова
  * `Word` - структура описания одного слова при сериализации машинного кода


## Транслятор

Интерфейс командной строки: 

```text
usage: translator.py [-h] [--output output_file] source_file

Translates code into en executable file.

positional arguments:
  source_file           file with source code

options:
  -h, --help            show this help message and exit
  --output output_file, -o output_file
                        file for storing an executable (default: output)
```

Реализовано в модуле: [translator](translator.py)

Этапы трансляции:
  * чтение исходного кода
  * удаление пустых строк и комментариев
  * извлечение секции с данными, секции с кодом
  * замена специальных инструкций (см. примечание к набору инструкций)
  * переупорядочивание аргументов (некоторые инструкции)
  * генерация слов машинного кода из инструкций
  * запись полученных слов в файл

При написании кода есть негласные правила:
* Аргументы в функцию передаются через регистры a0-a4, а если их не хватает, то оставшиеся передаются через стек
* Возвращаемое значение функции находится в регистре a0
* Все регистры (кроме `sp`) являются сaller-saved (т.е. при вызове функций не гарантируется сохранение этих регистров)


## Модель процессора

Интерфейс командной строки: 

```text
usage: machine.py [-h] [--input input_file] executable_file

Execute asm executable file.

positional arguments:
  executable_file       executable file

options:
  -h, --help            show this help message and exit
  --input input_file, -i input_file
                        file with input data for executable (default: empty file)
```

Реализовано в модуле: [machine](machine.py)

#### Data path

```text
                                                                                             +--------+
                                                                                       +-----|   ir   |
                   +-----------------------------------------------------------+       |     +--------+
                   |                                                           |       |
                   |  latch --->+--------+               +--------+<--- latch  |       |     +--------+<--- latch
                   |            |   a0   |-----+   +-----|   r0   |            |       +-----|   ip   |
                   +----------->+--------+     |   |     +--------+<-----------+       |     +--------+<-----------+
                   |                           |   |                           |       |                           |
                   |  latch --->+--------+     |   |     +--------+<--- latch  |       |     +--------+<--- latch  |
                   |            |   a1   |-----+   +-----|   r1   |            |       +-----|   ar   |            |
                   +----------->+--------+     |   |     +--------+<-----------+       |     +--------+<-----------+
                   |                           |   |                           |       |                           |
                   |  latch --->+--------+     |   |     +--------+<--- latch  |       |     +--------+<--- latch  |
                   |            |   a2   |-----+   +-----|   r2   |            |       +-----|   dr   |            |
                   |            +--------+     |   |     +--------+<-----------+       |     +--------+<-----------+
                   |                           |   |                           |       |                           |
                   |  latch --->+--------+     |   |     +--------+<--- latch  |       |     +--------+<--- latch  |
                   |            |   a3   |-----+   +-----|   r3   |            |       +-----|   sp   |            |
                   +----------->+--------+     |   |     +--------+<-----------+       |     +--------+<-----------+
                   |                           |   |                                   |                           |
                   |                           |   |   1   0   +-----------------------+                           |
                   |                           |   |   |   |   |                                                   |
                   |                           v   v   v   v   v                                                   |
                   |                        +-----------------------+                                              |
                   |                        |       CROSSBAR*       |                                              |
                   |                        +-----------------------+                                              |
                   |                             |             |                                                   |
                   |                             v             v                                                   |
         latch     |                        +---------+   +---------+                                              |
           |       |                        |          \_/          |                                              |
           v       |             alu_op --->|                       |                                              |  
       +-------+   |                        |          ALU          |                                              |
       |  flr  |<----------------------------\                     /                                               |
       +-------+   |                          +-------------------+                                                |
                   |                                    |                                                          |
                   +------------------------------------+----------------------------------------------------------+
```

**Примечание**: с целью упрощения схемы шины от регистров к АЛУ совмещены для нескольких регистров. Более правильно с
точки зрения схемотехники было бы вместо `CROSSBAR*` изобразить два мультиплексора на 13 входов каждый. Основная
идея - показать, что каждый регистр может поступить, как на левый, так и на правый входы АЛУ (теоретически и на оба).

#### Взаимодействие с памятью

```text
                                    read   write
                                      |      |
                                      v      v
                                  +------------+----------------------------------------------------------+
                          +------>| Comparator |                                                          |
                          |       +------------+------------------------------+                           |
                  sel     |           |      |                                |                           |
                   |      |   +--------------------------------------------------------------------+      |
                   v      |   |       v      v                                |                    |      |
   +--------+   +-----+   |   |   +------------+                              v read signal        v      v write signal
   |   ar   |-->| MUX |---+------>|            |                        +--------------+        +--------------+
   +--------+   +-----+       |   |            |            input ----->|    INPUT     |        |    OUTPUT    |-----> output
                              |   |   MEMORY   |                        |    BUFFER    |        |    BUFFER    |
                              |   |            |                        +--------------+        +--------------+
              +--------+      |   |            |                               |
   latch ---->|   dr   |------+-->|            |-------+   +-------------------+
              +--------+          +------------+       |   |
                   ^                                   |   |
                   |                                   |   |
                   |                                   |   |
                   |                                   v   v
                   |                                +---------+
                   +--------------------------------|   MUX   |<--- sel
                                                    +---------+
```

Реализован в классе `DataPath`.

Сигналы:
  * `read_memory` - чтение данных по адресу `ar` в `dr`:
    * из памяти (`dr <- mem[ar]`)
    * из порта ввода `input`:
      * извлечь из входного буфера токен и подать его на выход
      * если буфер пуст - исключение
  * `write_memory` - запись данных `dr` по адресу `ar`:
    * в память (`mem[ar] <- dr`)
    * в порт вывода `output`:
      * записать значение `dr` в буфер вывода
  * `latch_<reg>` - записать значение с выхода ALU (или памяти/буфера ввода) в регистр
  * `latch_fl` - записать значения флагов операции ALU в `fl`
  * `sel_addr` - выбрать адресный регистр для операции с памятью (`ar` или `ip`)
  * `sel_dr` - выбрать значение из памяти или буфера ввода для записи в `dr`
  * `alu_op` - выбор операции для осуществления на ALU (`sum`, `sub`, `div`, `mod`)


#### ControlUnit

```text
                                                                          +---------+
                                                                      +-->|  step   |--+                 input   output
                                                         latch        |   | counter |  |                   |       ^
         latch                   +--------------+          |          |   +---------+  v                   v       |
           |            read --->|              |          v          |     +---------------+  signals   +-----------+
           v                     |    MEMORY    |       +--------+    +-----|  instruction  |----------->| DataPath* |
        +--------+    +-----+    |              |------>|   ir   |--------->|    decoder    |            +-----------+
   +--->|   ip   |--->| MUX |--->|              |       +--------+          +---------------+               |    |
   |    +--------+    +-----+    +--------------+                                         ^                 |    |
   |                     ^                                                                |                 |    |
   |                     |                                                                +-----------------+    |
   |                    sel                                                                 feedback_signals     |
   |                                                                                                             |
   +-------------------------------------------------------------------------------------------------------------+
```

Реализован в классе `ControlUnit`.

Особенности:
  * hardwired (реализован полностью на Python, для каждого типа инструкции можно однозначно 
    определить сигналы и их порядок для каждого такта исполнения инструкции)
  * step counter - необходим для много-тактовых инструкций

Сигналы:
  * `read_memory` - чтение данных по адресу `ip` в `ir` (`ir <- mem[ip]`)
  * `latch_ir` - записать значение из памяти в `ir`
  * `sel_addr` - выбрать адресный регистр для операции с памятью
  * signals - управляющие сигналы в DataPath
  * feedback_signals - сигналы обратной связи (`fl`)

Шаг декодирования и исполнения одной инструкции выполняется в функции `execute_next_instruction`.
Во время шага в журнал моделирования записывается состояние модели и следующая исполняемая инструкция.

Цикл симуляции осуществляется в функции `simulation`.

Остановка моделирования осуществляется при превышении лимита количества выполняемых инструкций, 
при отсутствии данных для чтения из порта ввода, при выполнении инструкции `halt`.


## Тестирование

Для тестирования выбраны 4 базовых алгоритма:
1. [hello](./golden/hello.yml) ([source](./examples/hello))
2. [cat](./golden/cat.yml) ([source](./examples/cat))
3. [hello_user_name](./golden/hello_user_name.yml) ([source](./examples/hello_user_name))
4. [prob1](./golden/prob1.yml) ([source](./examples/prob1))

Golden-тесты реализованы в [integration_test.py](integration_test.py), конфигурация к ним 
находится в директории [golden](./golden).

CI реализован через GitHub Actions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:
* `poetry` - управления зависимостями для языка программирования Python.
* `coverage` - формирование отчёта об уровне покрытия исходного кода.
* `pytest` - утилита для запуска тестов.
* `ruff` - утилита для форматирования и проверки стиля кодирования.

Пример использования и журнал работы процессора на примере `cat`:

```bash
% cat ./examples/cat
section .text

start:
    mov *1001, *1000
    jmp start
    halt

% cat ./examples/input/cat
line


% python translator.py ./examples/cat
LoC: 6 code instr: 3

% cat output
[
  {
    "tag": "OPCODE",
    "op": "movmem2mem"
  },
  {
    "tag": "ARGUMENT",
    "arg": {
      "tag": "ADDRESS_EXACT",
      "val": 1000
    }
  },
  {
    "tag": "ARGUMENT",
    "arg": {
      "tag": "ADDRESS_EXACT",
      "val": 1001
    }
  },
  {
    "tag": "OPCODE",
    "op": "jmp"
  },
  {
    "tag": "ARGUMENT",
    "arg": {
      "tag": "NUMBER",
      "symbol": "start",
      "val": 0
    }
  },
  {
    "tag": "OPCODE",
    "op": "halt"
  }
]

% python machine.py ./output -i ./examples/input/cat
DEBUG:root:tick=0      ip=0x0     ar=0x0     dr=0x0     a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:MOVE_MEM_TO_MEM
DEBUG:root:input: 'l' <- 'ine\n'
DEBUG:root:output: '' <- 'l'
DEBUG:root:tick=9      ip=0x3     ar=0x3e9   dr=0x6c    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:JUMP
DEBUG:root:tick=12     ip=0x0     ar=0x3e9   dr=0x6c    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:MOVE_MEM_TO_MEM
DEBUG:root:input: 'i' <- 'ne\n'
DEBUG:root:output: 'l' <- 'i'
DEBUG:root:tick=21     ip=0x3     ar=0x3e9   dr=0x69    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:JUMP
DEBUG:root:tick=24     ip=0x0     ar=0x3e9   dr=0x69    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:MOVE_MEM_TO_MEM
DEBUG:root:input: 'n' <- 'e\n'
DEBUG:root:output: 'li' <- 'n'
DEBUG:root:tick=33     ip=0x3     ar=0x3e9   dr=0x6e    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:JUMP
DEBUG:root:tick=36     ip=0x0     ar=0x3e9   dr=0x6e    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:MOVE_MEM_TO_MEM
DEBUG:root:input: 'e' <- '\n'
DEBUG:root:output: 'lin' <- 'e'
DEBUG:root:tick=45     ip=0x3     ar=0x3e9   dr=0x65    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:JUMP
DEBUG:root:tick=48     ip=0x0     ar=0x3e9   dr=0x65    a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:MOVE_MEM_TO_MEM
DEBUG:root:input: '\n' <- ''
DEBUG:root:output: 'line' <- '\n'
DEBUG:root:tick=57     ip=0x3     ar=0x3e9   dr=0xa     a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:JUMP
DEBUG:root:tick=60     ip=0x0     ar=0x3e9   dr=0xa     a0=0x0     a1=0x0     a2=0x0     a3=0x0     r0=0x0     r1=0x0     r2=0x0     r3=0x0     sp=0x800   fl=0x0     stack_top=?
DEBUG:root:MOVE_MEM_TO_MEM
WARNING:root:Input buffer is empty
INFO:root:instr: 10 ticks: 63
line

```

Пример проверки исходного кода:

```bash
% poetry run pytest . -v
========================================================================================================= test session starts =========================================================================================================
platform win32 -- Python 3.11.0, pytest-7.4.4, pluggy-1.4.0 -- C:\Users\andrk\AppData\Local\pypoetry\Cache\virtualenvs\lispfuck-bFTolHPw-py3.11\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Programming\Projects\Python\ITMO\CompArchFall2023\asm
configfile: pyproject.toml
plugins: golden-0.2.2
collected 4 items                                                                                                                                                                                                                      

integration_test.py::test_translator_and_machine[golden/cat.yml] PASSED                                                                                                                                                          [ 25%]
integration_test.py::test_translator_and_machine[golden/hello.yml] PASSED                                                                                                                                                        [ 50%]
integration_test.py::test_translator_and_machine[golden/hello_user_name.yml] PASSED                                                                                                                                              [ 75%]
integration_test.py::test_translator_and_machine[golden/prob1.yml] PASSED                                                                                                                                                        [100%]

========================================================================================================== 4 passed in 5.06s ==========================================================================================================

% poetry run ruff check .

% poetry run ruff format .
4 files left unchanged
```

Статистика:

```text
| ФИО                    | алг   | LoC | code инстр. | инстр. | такт. | вариант                                                                           |
| Новиков Егор Сергеевич | hello | 22  | 12          | 92     | 446   | `asm | cisc | neum | hw | instr | struct | stream | mem | pstr | prob1 | [4]char` |
| Новиков Егор Сергеевич | cat   | 6   | 3           | 30     | 183   | `asm | cisc | neum | hw | instr | struct | stream | mem | pstr | prob1 | [4]char` |
| Новиков Егор Сергеевич | prob5 | 61  | 43          | 9031   | 49399 | `asm | cisc | neum | hw | instr | struct | stream | mem | pstr | prob1 | [4]char` |
```
