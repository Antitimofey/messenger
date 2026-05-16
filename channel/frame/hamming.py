import struct
from typing import Tuple, List

class Hamming74:
    """
    Реализация циклического кода Хэмминга [7,4].
    
    Структура кодового слова: [b3, b2, b1, b0, p0, p1, p2]
    где b3..b0 - информационные биты, p2..p0 - контрольные биты.
    
    Правила кодирования (соответствуют коду):
    p0 = b3 ⊕ b2 ⊕ b0
    p1 = b3 ⊕ b1 ⊕ b0
    p2 = b2 ⊕ b1 ⊕ b0
    """
    
    # Синдром (s2 s1 s0) -> Позиция бита в кодовом слове для инверсии (считая слева направо: b3=6, ..., p2=0)
    # Позиция для изменения вычисляется как (6 - error_pos), где error_pos указан в таблице.
    SYNDROME_TABLE = {
        0b001: 4,  # ошибка в p0 (позиция сдвига 2) -> 6 - 4 = 2
        0b010: 5,  # ошибка в p1 (позиция сдвига 1) -> 6 - 5 = 1
        0b100: 6,  # ошибка в p2 (позиция сдвига 0) -> 6 - 6 = 0
        0b011: 0,  # ошибка в b3 (позиция сдвига 6) -> 6 - 0 = 6
        0b101: 1,  # ошибка в b2 (позиция сдвига 5) -> 6 - 1 = 5
        0b110: 2,  # ошибка в b1 (позиция сдвига 4) -> 6 - 2 = 4
        0b111: 3,  # ошибка в b0 (позиция сдвига 3) -> 6 - 3 = 3
    }
    
    @classmethod
    def encode_4bits(cls, data_4bits: int) -> int:
        if data_4bits < 0 or data_4bits > 15:
            raise ValueError(f"data_4bits должен быть в диапазоне 0-15, получено {data_4bits}")
        
        b3 = (data_4bits >> 3) & 1
        b2 = (data_4bits >> 2) & 1
        b1 = (data_4bits >> 1) & 1
        b0 = data_4bits & 1
        
        p0 = b3 ^ b2 ^ b0
        p1 = b3 ^ b1 ^ b0
        p2 = b2 ^ b1 ^ b0
        
        codeword = (b3 << 6) | (b2 << 5) | (b1 << 4) | (b0 << 3) | (p0 << 2) | (p1 << 1) | p2
        return codeword
    
    @classmethod
    def decode_7bits(cls, codeword: int) -> Tuple[int, bool]:
        if codeword < 0 or codeword > 127:
            raise ValueError(f"codeword должен быть в диапазоне 0-127, получено {codeword}")
        
        b3 = (codeword >> 6) & 1
        b2 = (codeword >> 5) & 1
        b1 = (codeword >> 4) & 1
        b0 = (codeword >> 3) & 1
        p0 = (codeword >> 2) & 1
        p1 = (codeword >> 1) & 1
        p2 = codeword & 1
        
        r0 = b3 ^ b2 ^ b0
        r1 = b3 ^ b1 ^ b0
        r2 = b2 ^ b1 ^ b0
        
        s0 = p0 ^ r0
        s1 = p1 ^ r1
        s2 = p2 ^ r2
        syndrome = (s2 << 2) | (s1 << 1) | s0
        
        if syndrome == 0:
            data_4bits = (b3 << 3) | (b2 << 2) | (b1 << 1) | b0
            return data_4bits, False
        elif syndrome in cls.SYNDROME_TABLE:
            error_pos = cls.SYNDROME_TABLE[syndrome]
            corrected = codeword ^ (1 << (6 - error_pos))
            
            b3_corr = (corrected >> 6) & 1
            b2_corr = (corrected >> 5) & 1
            b1_corr = (corrected >> 4) & 1
            b0_corr = (corrected >> 3) & 1
            data_4bits = (b3_corr << 3) | (b2_corr << 2) | (b1_corr << 1) | b0_corr
            return data_4bits, True
        else:
            raise ValueError(f"Неисправимая ошибка: синдром {syndrome:03b}")
    
    @classmethod
    def encode_bytes(cls, data: bytes) -> bytes:
        result = bytearray()
        for byte in data:
            high_nibble = (byte >> 4) & 0x0F
            low_nibble = byte & 0x0F
            
            encoded_high = cls.encode_4bits(high_nibble)
            encoded_low = cls.encode_4bits(low_nibble)
            
            result.append((encoded_high << 1) | ((encoded_low >> 6) & 0x01))
            result.append((encoded_low & 0x3F) << 2)
        return bytes(result)
    
    @classmethod
    def decode_bytes(cls, encoded_data: bytes, original_len: int) -> bytes:
        result = bytearray()
        for i in range(0, len(encoded_data), 2):
            if i + 1 >= len(encoded_data):
                break
            
            byte1 = encoded_data[i]
            byte2 = encoded_data[i + 1]
            
            encoded_high = (byte1 >> 1) & 0x7F
            encoded_low = ((byte1 & 0x01) << 6) | (byte2 >> 2)
            
            high_nibble, _ = cls.decode_7bits(encoded_high)
            low_nibble, _ = cls.decode_7bits(encoded_low)
            
            original_byte = (high_nibble << 4) | low_nibble
            result.append(original_byte)
        return bytes(result[:original_len])







import unittest

class TestHamming74(unittest.TestCase):
    
    def test_encode_decode_clean(self):
        """Проверка кодирования и декодирования всех возможных 4-битных комбинаций без ошибок."""
        for data in range(16):
            codeword = Hamming74.encode_4bits(data)
            decoded_data, corrected = Hamming74.decode_7bits(codeword)
            
            self.assertEqual(data, decoded_data)
            self.assertFalse(corrected, "Флаг исправления должен быть False, так как ошибок не было.")

    def test_single_bit_error_correction(self):
        """Проверка исправления одиночной ошибки во всех 7 позициях для каждого числа."""
        for data in range(16):
            clean_codeword = Hamming74.encode_4bits(data)
            
            # Вносим ошибку в каждый из 7 бит по очереди
            for bit_pos in range(7):
                corrupted_codeword = clean_codeword ^ (1 << bit_pos)
                
                decoded_data, corrected = Hamming74.decode_7bits(corrupted_codeword)
                
                self.assertEqual(data, decoded_data, f"Не удалось исправить ошибку в бите {bit_pos} для данных {data}")
                self.assertTrue(corrected, f"Флаг исправления должен быть True для бита {bit_pos}")

    def test_value_errors(self):
        """Проверка генерации исключений при неверных диапазонах входных данных."""
        with self.assertRaises(ValueError):
            Hamming74.encode_4bits(16)
        with self.assertRaises(ValueError):
            Hamming74.encode_4bits(-1)
        with self.assertRaises(ValueError):
            Hamming74.decode_7bits(128)
        with self.assertRaises(ValueError):
            Hamming74.decode_7bits(-1)

    def test_bytes_encode_decode(self):
        """Проверка кодирования и декодирования массива байт."""
        test_bytes = b"Hello, Hamming [7,4]!"
        encoded = Hamming74.encode_bytes(test_bytes)
        
        # Длина закодированных данных должна быть в 2 раза больше (по логике упаковки в коде)
        self.assertEqual(len(encoded), len(test_bytes) * 2)
        
        decoded = Hamming74.decode_bytes(encoded, len(test_bytes))
        self.assertEqual(test_bytes, decoded)

if __name__ == "__main__":
    unittest.main()
