"""
В этом модуле хранятся функции для применения МНК
"""

from numbers import Real
from typing import Optional

from ..event_logger.event_logger import EventLogger

from .enumerations import MismatchStrategies
from .models import (
    LSMDescription,
    LSMLines,
)


PRECISION = 3                   # константа для точности вывода
event_logger = EventLogger()    # для логирования


def get_lsm_description(
    abscissa: list[float], ordinates: list[float],
    mismatch_strategy: MismatchStrategies = MismatchStrategies.FALL
) -> LSMDescription:

    """
    Функции для получения описания рассчитаной зависимости

    :param: abscissa - значения абсцисс
    :param: ordinates - значение ординат
    :param: mismatch_strategy - стратегия обработки несовпадения

    :return: структура типа LSMDescription
    """

    global event_logger
    #проверки
    if not (type(list(abscissa)) is list and type(list(ordinates)) is list):
        raise TypeError
    if not (_is_valid_measurments(abscissa) and
            _is_valid_measurments(ordinates)):
        raise ValueError
    if len(abscissa) != len(ordinates):
        abscissa, ordinates = _process_mismatch(abscissa, ordinates, mismatch_strategy)
    return _get_lsm_description(abscissa, ordinates)


def get_lsm_lines(
    abscissa: list[float], ordinates: list[float],
    lsm_description: Optional[LSMDescription] = None
) -> LSMLines:
    """
    Функция для расчета значений функций с помощью результатов МНК

    :param: abscissa - значения абсцисс
    :param: ordinates - значение ординат
    :param: lsm_description - описание МНК

    :return: структура типа LSMLines
    """
    a = lsm_description
    if a is None:
        a = get_lsm_description(abscissa, ordinates)
    #проверки
    if type(a) is not LSMDescription:
        raise TypeError
    pr1 = [(a.incline * i + a.shift) for i in abscissa]
    pr2 = [((a.incline + a.incline_error) * j +
                   a.shift + a.shift_error) for j in abscissa]
    pr3 = [((a.incline - a.incline_error) * _ +
                   a.shift - a.shift_error) for _ in abscissa]

    return LSMLines(
        abscissa=abscissa,
        ordinates=ordinates,
        line_predicted=pr1,
        line_above=pr2,
        line_under=pr3
    )


def get_report(
    lsm_description: LSMDescription, path_to_save: str = ''
) -> str:
    """
    Функция для формирования отчета о результатах МНК

    :param: lsm_description - описание МНК
    :param: path_to_save - путь к файлу для сохранения отчета

    :return: строка - отчет определенного формата
    """
    global PRECISION

    a = lsm_description
    report = '\n'.join([
        "=" * 40 + "LSM computing result" + "=" * 40 + "\n",
        "[INFO]: incline: " + f'{a.incline:.{PRECISION}f}' + ";",
        "[INFO]: shift: " + f'{a.shift:.{PRECISION}f}' + ";",
        "[INFO]: incline error: " + f'{a.incline_error:.{PRECISION}f}' + ";",
        "[INFO]: shift error: " + f'{a.shift_error:.{PRECISION}f}' + ";",
        "\n" + "=" * 100])

    if path_to_save != "":
        with open(path_to_save, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


# служебная функция для валидации
def _is_valid_measurments(measurments: list[float]) -> bool:
    m = measurments
    if (not (all(isinstance(i, Real) for i in m))) or (len(m) <= 2):
        return False
    return True

# служебная функция для обработки несоответствия размеров


def _process_mismatch(
    abscissa: list[float], ordinates: list[float],
    mismatch_strategy: MismatchStrategies = MismatchStrategies.FALL
) -> tuple[list[float], list[float]]:

    global event_logger

    if mismatch_strategy == MismatchStrategies.FALL:
        raise RuntimeError
    if mismatch_strategy == MismatchStrategies.CUT:
        if len(abscissa) > len(ordinates):
            abscissa = abscissa[:len(ordinates)]
        else:
            ordinates = ordinates[:len(abscissa)]
    else:
        raise ValueError
    return abscissa, ordinates


# служебная функция для получения описания МНК
def _get_lsm_description(
    abscissa: list[float], ordinates: list[float]
) -> LSMDescription:
    global event_logger, PRECISION

    a = len(abscissa)
    sm1 = sum(abscissa) / a
    sm2 = sum(ordinates) / a
    smxy = sum(abscissa[i] * ordinates[i] for i in range(a)) / a
    smx = sum(i ** 2 for i in abscissa) / a

    otv1 = int((smxy - sm1 * sm2) / (smx - sm1 ** 2))
    otv2 = sm2 - otv1 * sm1

    sigma_y2 = sum((ordinates[i] - otv1 * abscissa[i] - otv2) ** 2
                   for i in range(a)) / (a - 2)
    sigma_x = (sigma_y2 / ((smx - sm1 ** 2) * a)) ** 0.5
    sigma_y = ((sigma_y2 * smx) / ((smx - sm1 ** 2) * a)) ** 0.5
    return LSMDescription(
        incline=otv1,
        shift=otv2,
        incline_error=sigma_x,
        shift_error=sigma_y
    )
