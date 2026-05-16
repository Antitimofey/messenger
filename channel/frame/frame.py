
import struct
from enum import IntEnum
from typing import Optional, Tuple, List
import crcmod  # pip install crcmod
import unittest


# ============================================================================
# ЧАСТЬ 1: КЛАСС FRAME (КАДР ДАННЫХ)
# ============================================================================

class FrameType(IntEnum):
    """Типы кадров канального уровня"""
    DATA        = 0x01  # Данные (сообщение или часть файла)
    ACK         = 0x02  # Подтверждение приёма
    NAK         = 0x03  # Отрицательное подтверждение (ошибка)
    CONN_REQ    = 0x04  # Запрос установки соединения
    CONN_ACK    = 0x05  # Подтверждение соединения
    CONN_REL    = 0x06  # Разрыв соединения
    BCAST       = 0x07  # Широковещательное сообщение
    FILE_START  = 0x08  # Начало передачи файла
    FILE_END    = 0x09  # Конец передачи файла
    ERROR_NOTIFY= 0x0A  # Уведомление об ошибке


class Frame:
    """
    Класс кадра канального уровня.
    
    Формат кадра (байт):
    ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
    │  0x7E   │  DST    │  SRC    │  TYPE   │  LEN    │  DATA   │  CRC16  │  0x7E   │
    │  FLAG   │ (1 байт)│ (1 байт)│ (1 байт)│ (1 байт)│ (0-255) │(2 байта)│  FLAG   │
    └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
    
    Для широковещательной рассылки: DST = 0x00
    Адреса узлов: 0x01, 0x02, 0x03
    """
    
    FLAG_BYTE = b'\x7E'  # Флаг начала/конца кадра
    ESCAPE_BYTE = b'\x7D'  # Байт для эскапирования
    ESCAPE_MASK = 0x20  # Маска для эскапирования
    
    def __init__(self, dest_addr: int = None, src_addr: int = None, 
                 frame_type: FrameType = None, data: bytes = None,
                 raw_bytes: bytes = None):
        """
        Конструктор кадра - два режима работы.
        
        Режим 1: Создание кадра из параметров (для отправки)
        Режим 2: Десериализация кадра из сырых байт (для приёма)
        
        Параметры:
        ----------
        dest_addr : int, optional
            Адрес получателя (1-3) или 0 для широковещания
        src_addr : int, optional
            Адрес отправителя (1-3)
        frame_type : FrameType, optional
            Тип кадра
        data : bytes, optional
            Полезные данные (до 255 байт, для коротких сообщений - до 22)
        raw_bytes : bytes, optional
            Сырые байты для десериализации (при приёме)
            
        Исключения:
        -----------
        ValueError: Некорректные параметры или невалидный кадр
        """
        if raw_bytes is not None:
            # Режим 2: Десериализация из сырых байт
            self._deserialize(raw_bytes)
        else:
            # Режим 1: Создание из параметров
            if dest_addr is None or src_addr is None or frame_type is None:
                raise ValueError("При создании кадра необходимо указать dest_addr, src_addr и frame_type")
            
            self.dest_addr = dest_addr
            self.src_addr = src_addr
            self.type = frame_type
            self.data = data if data is not None else b''
            
            # Проверка длины данных (для коротких сообщений максимум 22 байта)
            if len(self.data) > 255:
                raise ValueError(f"Данные не могут превышать 255 байт (получено {len(self.data)})")
            
            # Данные для коротких сообщений не более 22 байт
            if frame_type == FrameType.DATA and len(self.data) > 22:
                raise ValueError(f"Короткое сообщение не может превышать 22 байта (получено {len(self.data)})")
    
    def _deserialize(self, raw_bytes: bytes):
        """
        Десериализация кадра из сырых байт (с учётом эскапирования).
        
        Вход:
        -----
        raw_bytes : bytes
            Сырые байты, полученные из порта (между флагами 0x7E)
            
        Выход:
        ------
        None (заполняет атрибуты объекта)
        
        Исключения:
        -----------
        ValueError: Некорректный формат кадра
        """
        # Проверка минимальной длины (флаг + DST + SRC + TYPE + LEN + CRC + флаг)
        if len(raw_bytes) < 6:
            raise ValueError(f"Кадр слишком короткий: {len(raw_bytes)} байт")
        
        # Деэскапирование данных (удаление ESCAPE байтов)
        raw_bytes = self._unescape(raw_bytes)
        
        # Распарсим заголовок (DST + SRC + TYPE + LEN) - 4 байта
        self.dest_addr = raw_bytes[0]
        self.src_addr = raw_bytes[1]
        self.type = FrameType(raw_bytes[2])
        data_len = raw_bytes[3]
        
        # Проверка длины
        if len(raw_bytes) < 4 + data_len + 2:  # заголовок + данные + CRC
            raise ValueError(f"Кадр повреждён: не хватает данных (ожидается {data_len}, получено {len(raw_bytes)-4-2})")
        
        # Извлекаем данные
        self.data = raw_bytes[4:4 + data_len]
        
        # Извлекаем и проверяем CRC
        received_crc = struct.unpack('>H', raw_bytes[4 + data_len:4 + data_len + 2])[0]
        
        # Вычисляем CRC для заголовка + данных
        calculated_crc = self._calculate_crc(raw_bytes[:4 + data_len])
        
        if received_crc != calculated_crc:
            raise ValueError(f"Ошибка CRC: ожидается {calculated_crc}, получено {received_crc}")
    
    def _escape(self, data: bytes) -> bytes:
        """
        Эскапирование байтов (байт-стаффинг).
        
        Правила:
        - 0x7E (FLAG) заменяется на 0x7D 0x5E
        - 0x7D (ESCAPE) заменяется на 0x7D 0x5D
        
        Вход:
        -----
        data : bytes
            Исходные данные
            
        Выход:
        ------
        bytes
            Данные с эскапированными служебными байтами
        """
        result = bytearray()
        for byte in data:
            if byte == 0x7E:  # FLAG
                result.append(0x7D)
                result.append(0x5E)
            elif byte == 0x7D:  # ESCAPE
                result.append(0x7D)
                result.append(0x5D)
            else:
                result.append(byte)
        return bytes(result)
    
    def _unescape(self, data: bytes) -> bytes:
        """
        Деэскапирование байтов (восстановление исходных данных).
        
        Вход:
        -----
        data : bytes
            Данные с эскапированными байтами
            
        Выход:
        ------
        bytes
            Восстановленные исходные данные
        """
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0x7D:  # ESCAPE
                if i + 1 >= len(data):
                    raise ValueError("Неожиданный конец данных после ESCAPE")
                next_byte = data[i + 1]
                if next_byte == 0x5E:
                    result.append(0x7E)
                elif next_byte == 0x5D:
                    result.append(0x7D)
                else:
                    raise ValueError(f"Некорректный эскапированный байт: {next_byte:02X}")
                i += 2
            else:
                result.append(data[i])
                i += 1
        return bytes(result)
    
    def _calculate_crc(self, data: bytes) -> int:
        """
        Вычисление CRC-16 для проверки целостности кадра.
        
        Вход:
        -----
        data : bytes
            Данные для вычисления CRC (заголовок + полезные данные)
            
        Выход:
        ------
        int
            16-битное CRC-значение
        """
        # Используем CRC-16-IBM (x^16 + x^15 + x^2 + 1)
        crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        return crc16_func(data)
    
    def serialize(self) -> bytes:
        """
        Сериализация кадра в байты для отправки через физический уровень.
        
        Выход:
        ------
        bytes
            Полный кадр с флагами и эскапированием
        
        Формат вывода:
        [0x7E][ESC_FRAME][0x7E]
        """
        # Собираем заголовок + данные
        header = bytes([
            self.dest_addr,
            self.src_addr,
            self.type,
            len(self.data)
        ])
        
        # Вычисляем CRC
        crc = self._calculate_crc(header + self.data)
        crc_bytes = struct.pack('>H', crc)
        
        # Собираем кадр без флагов
        raw_frame = header + self.data + crc_bytes
        
        # Эскапируем служебные байты
        escaped_frame = self._escape(raw_frame)
        
        # Добавляем флаги в начало и конец
        return self.FLAG_BYTE + escaped_frame + self.FLAG_BYTE
    
    def is_broadcast(self) -> bool:
        """Проверка, является ли кадр широковещательным"""
        return self.dest_addr == 0x00
    
    def is_for_me(self, my_addr: int) -> bool:
        """Проверка, адресован ли кадр текущему узлу"""
        return self.dest_addr == my_addr or self.is_broadcast()
    
    def __repr__(self) -> str:
        return (f"Frame(dest={self.dest_addr:02X}, src={self.src_addr:02X}, "
                f"type={self.type.name}, data_len={len(self.data)})")
    
    def get_data_as_text(self) -> str:
        """
        Получение данных кадра как текст (для коротких сообщений).
        
        Выход:
        ------
        str
            Декодированный текст сообщения
        """
        try:
            return self.data.decode('utf-8', errors='replace')
        except:
            return str(self.data)









# ============================================================================
# ТЕСТЫ С ПОДРОБНЫМИ КОММЕНТАРИЯМИ
# ============================================================================

class TestFrame(unittest.TestCase):
    """
    Набор тестов для проверки класса Frame.
    Каждый тест проверяет конкретный аспект работы кадров канального уровня.
    """
    
    def test_create_and_serialize(self):
        """
        ТЕСТ №1: Создание кадра из параметров и сериализация
        
        Что проверяет:
        - Корректность создания кадра через конструктор с параметрами
        - Правильность установки всех полей (адреса, тип, данные)
        - Наличие флагов 0x7E в начале и конце сериализованного кадра
        
        Логика:
        1. Создаём кадр с явными параметрами (адрес назначения=0x01, источник=0x02, 
           тип=DATA, данные=Hello)
        2. Проверяем, что все поля установлены правильно
        3. Сериализуем кадр в байтовую строку
        4. Проверяем, что сериализованные данные начинаются и заканчиваются флагом 0x7E
        
        Ожидаемый результат: Все проверки проходят успешно
        """
        frame = Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.DATA, data=b'Hello')
        self.assertEqual(frame.dest_addr, 0x01)
        self.assertEqual(frame.src_addr, 0x02)
        self.assertEqual(frame.type, FrameType.DATA)
        self.assertEqual(frame.data, b'Hello')
        serialized = frame.serialize()
        self.assertTrue(serialized.startswith(b'\x7E'))
        self.assertTrue(serialized.endswith(b'\x7E'))
    
    def test_deserialize_valid_frame(self):
        """
        ТЕСТ №2: Десериализация корректного кадра (обратное преобразование)
        
        Что проверяет:
        - Возможность восстановить кадр из байтовой последовательности
        - Сохранение всех полей при сериализации/десериализации
        - Работу алгоритмов эскапирования и CRC
        
        Логика:
        1. Создаём исходный кадр с типом ACK и данными OK
        2. Сериализуем его в байты
        3. Удаляем флаги (получаем "сырые" байты между флагами)
        4. Создаём новый кадр из этих байт через raw_bytes
        5. Сравниваем все поля восстановленного кадра с исходным
        
        Ожидаемый результат: Поля совпадают, данные не повреждены
        """
        original = Frame(dest_addr=0x03, src_addr=0x01, frame_type=FrameType.ACK, data=b'OK')
        serialized = original.serialize()
        # Убираем флаги для передачи в raw_bytes
        raw_without_flags = serialized[1:-1]
        restored = Frame(raw_bytes=raw_without_flags)
        self.assertEqual(restored.dest_addr, original.dest_addr)
        self.assertEqual(restored.src_addr, original.src_addr)
        self.assertEqual(restored.type, original.type)
        self.assertEqual(restored.data, original.data)
    
    def test_escape_unescape(self):
        """
        ТЕСТ №3: Эскапирование и деэскапирование служебных байтов
        
        Что проверяет:
        - Правильность замены байтов 0x7E и 0x7D
        - Корректное восстановление исходных данных
        
        Что такое эскапирование:
        Байты 0x7E и 0x7D имеют специальное значение (флаг и escape), поэтому
        если они встречаются в данных, их нужно заменять на двухбайтовые
        последовательности:
        - 0x7E -> 0x7D 0x5E
        - 0x7D -> 0x7D 0x5D
        
        Логика:
        1. Берём данные, содержащие служебные байты: 0x7E, 0x7D
        2. Применяем эскапирование
        3. Проверяем, что получена правильная заменённая последовательность
        4. Применяем деэскапирование
        5. Проверяем, что данные восстановлены без потерь
        
        Ожидаемый результат: Исходные и восстановленные данные идентичны
        """
        data = b'\x7E\x7DHello\x7E'
        escaped = Frame._escape(Frame, data)
        self.assertEqual(escaped, b'\x7D\x5E\x7D\x5DHello\x7D\x5E')
        unescaped = Frame._unescape(Frame, escaped)
        self.assertEqual(unescaped, data)
    
    def test_broadcast(self):
        """
        ТЕСТ №4: Широковещательная рассылка (broadcast)
        
        Что проверяет:
        - Правильность определения широковещательного кадра (dest=0x00)
        - Что широковещательный кадр доставляется всем узлам
        
        Логика:
        1. Создаём кадр с адресом назначения 0x00 (broadcast)
        2. Проверяем, что метод is_broadcast() возвращает True
        3. Проверяем, что кадр считается адресованным для узлов с разными адресами
           (0x01, 0x02) - т.е. все узлы должны принимать broadcast
        
        Ожидаемый результат: is_broadcast() = True, is_for_me() = True для любых адресов
        """
        frame = Frame(dest_addr=0x00, src_addr=0x02, frame_type=FrameType.BCAST, data=b'ALL')
        self.assertTrue(frame.is_broadcast())
        self.assertTrue(frame.is_for_me(0x01))
        self.assertTrue(frame.is_for_me(0x02))
    
    def test_is_for_me(self):
        """
        ТЕСТ №5: Адресация кадров
        
        Что проверяет:
        - Правильность проверки, адресован ли кадр конкретному узлу
        
        Логика:
        1. Создаём кадр, адресованный узлу 0x03
        2. Проверяем, что для узла 0x03 кадр адресован (is_for_me = True)
        3. Проверяем, что для узла 0x02 кадр НЕ адресован (is_for_me = False)
        
        Важно: Широковещательные кадры проверяются в отдельном тесте
        
        Ожидаемый результат: Только узел с совпадающим адресом получает кадр
        """
        frame = Frame(dest_addr=0x03, src_addr=0x01, frame_type=FrameType.DATA)
        self.assertTrue(frame.is_for_me(0x03))
        self.assertFalse(frame.is_for_me(0x02))
    
    def test_crc_error(self):
        """
        ТЕСТ №6: Обнаружение ошибок через CRC
        
        Что проверяет:
        - Что кадр с повреждёнными данными отвергается
        - Что выбрасывается исключение с информацией об ошибке CRC
        
        Что такое CRC: Контрольная сумма, позволяющая обнаружить
        случайные ошибки в переданных данных
        
        Логика:
        1. Создаём корректный кадр
        2. Сериализуем его
        3. Повреждаем один байт в данных (меняем его значение)
        4. Пытаемся десериализовать повреждённый кадр
        5. Проверяем, что возникает ошибка ValueError с упоминанием CRC
        
        Ожидаемый результат: Выброшено исключение ValueError с текстом об ошибке CRC
        """
        frame = Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.DATA, data=b'data')
        serialized = frame.serialize()
        raw = serialized[1:-1]  # без флагов
        # Повреждаем один байт в данных (XOR с 0xFF инвертирует биты)
        corrupted = raw[:5] + bytes([raw[5] ^ 0xFF]) + raw[6:]
        with self.assertRaises(ValueError) as ctx:
            Frame(raw_bytes=corrupted)
        self.assertIn("CRC", str(ctx.exception))
    
    def test_short_frame(self):
        """
        ТЕСТ №7: Кадр с пустыми данными (минимальной длины)
        
        Что проверяет:
        - Обработку кадров без полезных данных (LEN=0)
        - Корректность проверки минимальной длины (должна быть 6, а не 7 байт)
        
        Структура кадра без данных (6 байт):
        - DST (1) + SRC (1) + TYPE (1) + LEN=0 (1) = 4 байта
        - CRC (2) = 2 байта
        Итого: 6 байт
        
        Логика:
        1. Создаём кадр типа ACK с пустыми данными
        2. Сериализуем его
        3. Извлекаем сырые байты без флагов (должно быть 6 байт)
        4. Восстанавливаем кадр
        5. Проверяем, что данные пустые и тип сохранился
        
        Ожидаемый результат: Кадр успешно десериализуется, data = b''
        """
        frame = Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.ACK, data=b'')
        serialized = frame.serialize()
        raw = serialized[1:-1]
        self.assertEqual(len(raw), 6)  # 4 байта заголовка + 2 байта CRC
        restored = Frame(raw_bytes=raw)
        self.assertEqual(restored.data, b'')
        self.assertEqual(restored.type, FrameType.ACK)
    
    def test_data_length_limit(self):
        """
        ТЕСТ №8: Ограничения длины данных
        
        Что проверяет:
        - Запрет на слишком длинные данные (>255 байт)
        - Специальное ограничение для типа DATA (≤22 байта)
        - Разрешены длинные данные для других типов кадров (например, FILE_START)
        
        Логика:
        1. Пытаемся создать кадр типа DATA с 23 байтами -> ожидаем ошибку
        2. Создаём кадр типа FILE_START со 100 байтами -> ошибки не должно быть
        
        Почему 22 байта для DATA: Это ограничение для коротких сообщений,
        характерное для некоторых протоколов канального уровня
        
        Ожидаемый результат: 
        - DATA с 23 байтами вызывает ValueError
        - FILE_START со 100 байтами успешно создаётся
        """
        with self.assertRaises(ValueError):
            Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.DATA, data=b'x'*23)
        # Длинные данные для другого типа кадра допустимы (до 255)
        large_data = b'x' * 100
        frame = Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.FILE_START, data=large_data)
        self.assertEqual(len(frame.data), 100)
    
    def test_unescape_invalid(self):
        """
        ТЕСТ №9: Обработка неверных эскапированных последовательностей
        
        Что проверяет:
        - Что при получении некорректной эскапированной последовательности
          выбрасывается исключение
        
        Некорректная последовательность: ESCAPE (0x7D) за которым следует
        недопустимый байт (не 0x5E и не 0x5D)
        
        Логика:
        1. Создаём неверную эскапированную последовательность: 0x7D 0xFF
        2. Пытаемся деэскапировать её
        3. Проверяем, что возникает ValueError
        
        Ожидаемый результат: Исключение ValueError с информацией об ошибке
        """
        invalid = b'\x7D\xFF'
        with self.assertRaises(ValueError):
            Frame._unescape(Frame, invalid)
    
    def test_get_data_as_text(self):
        """
        ТЕСТ №10: Декодирование текстовых данных из кадра
        
        Что проверяет:
        - Преобразование байтовых данных в строку UTF-8
        - Корректность работы с кириллическими символами
        
        Важно: Используем .encode('utf-8') для создания байтовой строки
        из не-ASCII символов
        
        Логика:
        1. Создаём кадр с русским текстом (кодируем в UTF-8)
        2. Вызываем метод get_data_as_text()
        3. Проверяем, что декодированный текст совпадает с исходным
        
        Ожидаемый результат: Русский текст корректно декодируется
        """
        text = 'Привет'
        frame = Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.DATA, 
                     data=text.encode('utf-8'))
        self.assertEqual(frame.get_data_as_text(), text)
    
    def test_empty_data_serialization(self):
        """
        ТЕСТ №11: Сериализация пустых данных
        
        Что проверяет:
        - Что кадр с пустыми данными сериализуется в правильный размер
        - Проверка точной длины сериализованного кадра
        
        Расчёт размера:
        - Флаг начала: 1 байт (0x7E)
        - Заголовок + CRC: 6 байт (DST, SRC, TYPE, LEN=0, CRC)
        - Флаг конца: 1 байт (0x7E)
        - Итого: 8 байт
        
        Логика:
        1. Создаём кадр типа NAK с пустыми данными
        2. Сериализуем
        3. Проверяем, что длина равна 8 байтам
        4. Извлекаем сырые байты между флагами
        5. Восстанавливаем кадр и проверяем пустые данные
        
        Ожидаемый результат: Длина = 8, восстановленный кадр имеет data = b''
        """
        frame = Frame(dest_addr=0x01, src_addr=0x02, frame_type=FrameType.NAK, data=b'')
        serialized = frame.serialize()
        # 1 флаг + 6 байт кадра + 1 флаг = 8 байт
        self.assertEqual(len(serialized), 8)
        raw = serialized[1:-1]
        restored = Frame(raw_bytes=raw)
        self.assertEqual(restored.data, b'')


if __name__ == "__main__":
    """
    Точка входа при запуске скрипта.
    
    unittest.main() автоматически:
    1. Находит все классы, наследующие unittest.TestCase
    2. Запускает все методы, начинающиеся с 'test_'
    3. Выводит отчёт о прохождении тестов
    4. Возвращает код возврата: 0 (успех) или 1 (ошибка)
    
    Для запуска из терминала:
    $ python3 frame.py
    
    Для запуска с подробным выводом:
    $ python3 frame.py -v
    """
    unittest.main()