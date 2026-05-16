
import struct
from enum import IntEnum
from typing import Optional, Tuple, List
import crcmod  # pip install crcmod
import unittest
from .frame import Frame, FrameType
from hamming import Hamming74



class EncryptedFrame(Frame):
    """
    Класс кадра канального уровня с помехоустойчивым кодированием Хэмминга [7,4].
    
    При сериализации: заголовок, данные и CRC базового кадра кодируются 
    с помощью Hamming74, после чего результат эскапируется и обрамляется флагами.
    
    При десериализации: сырые байты деэскапируются, декодируются кодом Хэмминга 
    с исправлением одиночных ошибок, а затем парсятся базовым классом Frame.
    """
    
    def __init__(self, dest_addr: int = None, src_addr: int = None, 
                 frame_type: FrameType = None, data: bytes = None,
                 raw_bytes: bytes = None):
        """
        Переопределенный конструктор.
        Поддерживает создание из параметров или десериализацию из зашифрованных байт.
        """
        if raw_bytes is not None:
            # Режим 2: Десериализация из зашифрованных сырых байт
            self._encrypted_deserialize(raw_bytes)
        else:
            # Режим 1: Обычная инициализация через базовый класс
            super().__init__(dest_addr=dest_addr, src_addr=src_addr, 
                             frame_type=frame_type, data=data)

    def _encrypted_deserialize(self, raw_bytes: bytes):
        """
        Десериализация зашифрованного кадра с исправлением ошибок.
        """
        # 1. Минимальная проверка (Флаг + хотя бы 1 байт + Флаг)
        if len(raw_bytes) < 3:
            raise ValueError(f"Зашифрованный кадр слишком короткий: {len(raw_bytes)} байт")
            
        # Убираем внешние флаги, если они пришли вместе с raw_bytes
        if raw_bytes.startswith(self.FLAG_BYTE) and raw_bytes.endswith(self.FLAG_BYTE):
            raw_bytes = raw_bytes[1:-1]
            
        # 2. Деэскапируем байты (базовая функция Frame)
        unescaped_hamming_bytes = self._unescape(raw_bytes)
        
        # 3. Так как заголовок (4 байта) кодируется в 8 байт Хэмминга, 
        #    мы можем сначала декодировать первые 8 байт, чтобы узнать длину данных (LEN).
        if len(unescaped_hamming_bytes) < 8:
            raise ValueError("Недостаточно данных для декодирования заголовка Хэмминга")
            
        decoded_header = Hamming74.decode_bytes(unescaped_hamming_bytes[:8], original_len=4)
        data_len = decoded_header[3]
        
        # Вычисляем полную ожидаемую длину исходного кадра (Заголовок(4) + DATA(data_len) + CRC(2))
        total_original_len = 4 + data_len + 2
        # В коде Hamming74 каждый исходный байт превращается в 2 байта
        total_hamming_len = total_original_len * 2
        
        if len(unescaped_hamming_bytes) < total_hamming_len:
            raise ValueError(f"Кадр поврежден: ожидалось {total_hamming_len} байт Хэмминга, получено {len(unescaped_hamming_bytes)}")
            
        # 4. Декодируем весь пакет целиком и исправляем ошибки
        clean_frame_bytes = Hamming74.decode_bytes(unescaped_hamming_bytes[:total_hamming_len], original_len=total_original_len)
        
        # 5. Передаем чистые байты в стандартный парсер базового класса для валидации CRC и наполнения полей
        # Для этого временно подделываем вызов _deserialize, но передаем байты БЕЗ эскапирования,
        # поэтому переопределим шаг деэскапирования внутри этой цепочки, либо напрямую распарсим.
        # Чтобы не дублировать код валидации CRC и полей, вызовем внутренний разбор:
        self._parse_clean_bytes(clean_frame_bytes)

    def _parse_clean_bytes(self, clean_bytes: bytes):
        """Вспомогательный метод парсинга массива байт, где уже нет Хэмминга и ESCAPE"""
        self.dest_addr = clean_bytes[0]
        self.src_addr = clean_bytes[1]
        self.type = FrameType(clean_bytes[2])
        data_len = clean_bytes[3]
        
        self.data = clean_bytes[4:4 + data_len]
        
        received_crc = struct.unpack('>H', clean_bytes[4 + data_len:4 + data_len + 2])[0]
        calculated_crc = self._calculate_crc(clean_bytes[:4 + data_len])
        
        if received_crc != calculated_crc:
            raise ValueError(f"Ошибка CRC внутри декодированного кадра: ожидается {calculated_crc}, получено {received_crc}")

    def encrypted_serialize(self) -> bytes:
        """
        Сериализация кадра с защитой кодом Хэмминга.
        
        Формат: [0x7E] + ESCAPE( HAMMING( Заголовок + Данные + CRC ) ) + [0x7E]
        """
        # 1. Собираем чистый заголовок
        header = bytes([
            self.dest_addr,
            self.src_addr,
            self.type,
            len(self.data)
        ])
        
        # 2. Считаем контрольную сумму базового кадра
        crc = self._calculate_crc(header + self.data)
        crc_bytes = struct.pack('>H', crc)
        
        clean_frame = header + self.data + crc_bytes
        
        # 3. Кодируем кодом Хэмминга
        hamming_encoded = Hamming74.encode_bytes(clean_frame)
        
        # 4. Эскапируем результат (чтобы внутри Хэмминга случайно не вылезли байты 0x7E или 0x7D)
        escaped_bytes = self._escape(hamming_encoded)
        
        # 5. Оборачиваем во флаги физического уровня
        return self.FLAG_BYTE + escaped_bytes + self.FLAG_BYTE







class TestEncryptedFrame(unittest.TestCase):
    
    def test_encrypted_serialization_flow(self):
        """Проверка сквозного цикла: создание -> шифрование -> десериализация"""
        data_to_send = b"Secret Message"
        frame_src = EncryptedFrame(
            dest_addr=0x02, 
            src_addr=0x01, 
            frame_type=FrameType.DATA, 
            data=data_to_send
        )
        
        # Шифруем и сериализуем
        wire_bytes = frame_src.encrypted_serialize()
        
        # Принимаем и десериализуем
        frame_dst = EncryptedFrame(raw_bytes=wire_bytes)
        
        # Проверяем идентичность полей
        self.assertEqual(frame_dst.dest_addr, 0x02)
        self.assertEqual(frame_dst.src_addr, 0x01)
        self.assertEqual(frame_dst.type, FrameType.DATA)
        self.assertEqual(frame_dst.data, data_to_send)

    def test_error_correction_in_frame(self):
        """Тест симуляции помех: внесение одиночной битовой ошибки в закодированное тело кадра"""
        data_to_send = b"Validating Hamming..."
        frame_src = EncryptedFrame(
            dest_addr=0x03, 
            src_addr=0x01, 
            frame_type=FrameType.DATA, 
            data=data_to_send
        )
        
        wire_bytes = frame_src.encrypted_serialize()
        
        # Модифицируем wire_bytes: вносим ошибку внутрь Хэмминг-структуры.
        # Нам нужно внести ошибку ПОСЛЕ деэскапирования (или выбрать байт, который не является флагом/escape)
        # Для простоты превратим wire_bytes в bytearray, снимем флаги, внесем ошибку в случайный бит 5-го байта.
        payload = bytearray(wire_bytes[1:-1])
        
        # Искажаем 1 бит в 5-м байте данных (это точно часть закодированного Хэммингом сообщения)
        payload[5] ^= 0x04 
        
        # Собираем кадр обратно с флагами
        corrupted_wire_bytes = Frame.FLAG_BYTE + bytes(payload) + Frame.FLAG_BYTE
        
        # Декодирование должно пройти УСПЕШНО, так как Хэмминг исправит этот бит
        frame_dst = EncryptedFrame(raw_bytes=corrupted_wire_bytes)
        
        self.assertEqual(frame_dst.data, data_to_send, "Код Хэмминга не смог восстановить поврежденный бит в кадре!")

def test_corrupted_frame_double_error(self):
        """Тест двойной ошибки: Хэмминг должен ложно исправить, но CRC обязан отсечь пакет"""
        frame_src = EncryptedFrame(
            dest_addr=0x01, 
            src_addr=0x02, 
            frame_type=FrameType.DATA, 
            data=b"Unbreakable?"
        )
        wire_bytes = frame_src.encrypted_serialize()
        payload = bytearray(wire_bytes[1:-1])
        
        # Гарантированно бьем значащие биты в первом байтов Хэмминг-пары.
        # Изменяем 6-й и 7-й биты в payload[0], которые отвечают за старшую тетраду DST.
        # Это вызовет ложное исправление Хэмминга -> данные изменятся -> CRC не совпадет.
        payload[0] ^= 0x40  # 6-й бит
        payload[0] ^= 0x80  # 7-й бит
        
        corrupted_wire_bytes = Frame.FLAG_BYTE + bytes(payload) + Frame.FLAG_BYTE
        
        # Теперь исключение ValueError гарантированно вылетит (из-за несовпадения CRC)
        with self.assertRaises(ValueError):
            EncryptedFrame(raw_bytes=corrupted_wire_bytes)



if __name__ == "__main__":
    unittest.main()