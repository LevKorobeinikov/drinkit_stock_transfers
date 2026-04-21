from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditItem:
    code: str
    title: str
    max_score: int


@dataclass(frozen=True)
class AuditBlock:
    index: int
    title: str
    items: tuple[AuditItem, ...]

    @property
    def max_score(self) -> int:
        return sum(item.max_score for item in self.items)


AUDIT_BLOCKS: tuple[AuditBlock, ...] = (
    AuditBlock(
        index=1,
        title="У входа (выберет ли гость Drinkit с первого взгляда?)",
        items=(
            AuditItem("1.1", "Заметный фасад", 1),
            AuditItem("1.2", "Чистая входная группа", 3),
            AuditItem("1.3", "Приветствие при входе", 2),
            AuditItem("1.4", "Интуитивно понятное расположение планшетов", 1),
            AuditItem("1.5", "Музыка на комфортной громкости", 1),
            AuditItem("1.6", "Нет посторонних запахов", 1),
        ),
    ),
    AuditBlock(
        index=2,
        title="У кассы (насколько удобно делать заказ?)",
        items=(
            AuditItem("2.1", "Бариста уточнил знакомство с Drinkit/нужна ли помощь", 1),
            AuditItem("2.2", "Рассказали про приложение (установка/QR)", 1),
            AuditItem("2.3", "Бариста знает ассортимент и может рекомендовать", 2),
            AuditItem("2.4", "Планшеты работают исправно", 3),
            AuditItem("2.5", "Планшеты чистые", 2),
            AuditItem("2.6", "Кондименты пополнены", 1),
            AuditItem("2.7", "Мусорки не переполнены", 1),
            AuditItem("2.8", "Стопы актуальны", 2),
        ),
    ),
    AuditBlock(
        index=3,
        title="У места гостя (что влияет на комфорт?)",
        items=(
            AuditItem("3.1", "Чистые столики", 2),
            AuditItem("3.2", "Чистые полы и стены", 3),
            AuditItem("3.3", "Убрано в туалете (чистота и пополнение)", 1),
            AuditItem("3.4", "Наличие розеток, заметное расположение", 1),
            AuditItem("3.5", "Комфортная температура в зале", 1),
            AuditItem("3.6", "Нет громкого шума с бара", 1),
        ),
    ),
    AuditBlock(
        index=4,
        title="Выдача (вкус и визуальное впечатление)",
        items=(
            AuditItem("4.1", "Время ожидания (до 5 минут при низкой нагрузке)", 4),
            AuditItem("4.2", "Заказ объявили по имени и выдали в нужную ячейку", 2),
            AuditItem("4.3", "Напиток с правильным кастомайзом", 2),
            AuditItem("4.4", "Напиток соответствует стандарту (латте-арт)", 2),
            AuditItem("4.5", "Температура напитка соответствует норме", 2),
            AuditItem("4.6", "Еда хорошо прогрета (если требуется)", 2),
            AuditItem("4.7", "Срок годности еды в порядке", 3),
            AuditItem("4.8", "На баре порядок (вне пика)", 2),
            AuditItem("4.9", "Внешний вид бариста опрятный, форма чистая", 2),
            AuditItem("4.10", "Выдача чистая", 2),
        ),
    ),
    AuditBlock(
        index=5,
        title="У выхода (с какими эмоциями гость уходит?)",
        items=(
            AuditItem("5.1", "Входная группа всё ещё чистая", 1),
            AuditItem("5.2", "Мусорки не переполнены", 1),
            AuditItem("5.3", "Попрощались", 2),
        ),
    ),
)
