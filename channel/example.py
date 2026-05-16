
# ==============================================
# КАНАЛЬНЫЙ УРОВЕНЬ (разработчик Антипов Т.И.)
# ==============================================
class DataLinkLayer:
    """
    Канальный уровень.
    НЕ СОЗДАЁТ потоков, просто регистрирует callback в физическом уровне.
    """
    
    def __init__(self, input_port: COMPort, output_port: COMPort, my_address: int):
        self.input_port = input_port   # Уже созданный экземпляр COMPort
        self.output_port = output_port # Уже созданный экземпляр COMPort
        self.my_address = my_address
        
    def start(self):
        """Запуск канального уровня"""
        # Регистрируем callback в физическом уровне
        # Физический уровень сам будет вызывать его из своего потока
        self.input_port.set_receive_callback(self._on_frame_received)
        print("[LINK] Канальный уровень запущен, callback зарегистрирован")
    
    def _on_frame_received(self, raw_bytes: bytes):
        """
        Этот метод будет вызываться ИЗ ПОТОКА ФИЗИЧЕСКОГО УРОВНЯ.
        Канальный уровень должен быть готов к этому.
        """
        # Здесь обработка кадра
        print(f"[LINK] Получено {len(raw_bytes)} байт из потока физического уровня")
        
        # Анализ кадра...
        # Если кадр не мне - ретранслируем
        # Если мне - отдаём прикладному уровню
    
    def send_frame(self, dest_addr: int, data: bytes):
        """Отправка кадра (вызывается из главного потока)"""
        # Формируем кадр...
        frame = self._build_frame(dest_addr, data)
        
        # Отправляем через физический уровень
        self.output_port.send_bytes(frame)


# ==============================================
# ГЛАВНАЯ ПРОГРАММА (сборка всей системы)
# ==============================================
def main():
    # 1. Физический уровень создаёт порты (потоки запустятся внутри)
    input_port = COMPort('input')
    output_port = COMPort('output')
    
    # 2. Открываем порты (внутри запустятся потоки для input)
    input_port.open_port('COM1', 9600)
    output_port.open_port('COM2', 9600)
    
    # 3. Канальный уровень получает уже готовые порты
    link_layer = DataLinkLayer(input_port, output_port, my_address=1)
    
    # 4. Канальный уровень запускается (регистрирует callback)
    link_layer.start()
    
    # 5. Работаем...
    link_layer.send_frame(dest_addr=2, data=b"Hello")
    
    # 6. Завершение
    input_port.close_port()
    output_port.close_port()