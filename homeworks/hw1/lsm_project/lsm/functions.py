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

    if not (type(list(abscissa)) is list and type(list(ordinates)) is list):
        raise TypeError

    if not (_is_valid_measurments(abscissa) and
            _is_valid_measurments(ordinates)):
        raise ValueError

    if len(abscissa) != len(ordinates):
        abscissa, ordinates = \
            _process_mismatch(abscissa, ordinates, mismatch_strategy)

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
    if lsm_description is None:
        lsm_description = get_lsm_description(abscissa, ordinates)
    if type(lsm_description) is not LSMDescription:
        raise TypeError
    line_predicted = [(lsm_description.incline*x + lsm_description.shift) for x in abscissa]
    line_above = [((lsm_description.incline+lsm_description.incline_error)*x +
                   lsm_description.shift + lsm_description.shift_error) for x in abscissa]
    line_under = [((lsm_description.incline-lsm_description.incline_error)*x +
                   lsm_description.shift - lsm_description.shift_error) for x in abscissa]

    return LSMLines(
        abscissa=abscissa,
        ordinates=ordinates,
        line_predicted=line_predicted,
        line_above=line_above,
        line_under=line_under
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

    report = '\n'.join([
        "="*40 + "LSM computing result" + "="*40 + "\n",
        "[INFO]: incline: " + f'{lsm_description.incline:.{PRECISION}f}' + ";",
        "[INFO]: shift: " + f'{lsm_description.shift:.{PRECISION}f}' + ";",
        "[INFO]: incline error: " + f'{lsm_description.incline_error:.{PRECISION}f}' + ";",
        "[INFO]: shift error: " + f'{lsm_description.shift_error:.{PRECISION}f}' + ";",
        "\n" + "="*100
    ])

    if path_to_save != "":
        with open(path_to_save, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


# служебная функция для валидации
def _is_valid_measurments(measurments: list[float]) -> bool:
    if not (all(isinstance(i, Real) for i in measurments)):
        return False
    if len(measurments) <= 2:
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

    n = len(abscissa)
    x = sum(abscissa) / n
    y = sum(ordinates) / n
    xy = sum(abscissa[i] * ordinates[i] for i in range(n)) / n
    x2 = sum(i ** 2 for i in abscissa) / n

    a = (xy - x * y) / (x2 - x ** 2)
    b = y - a * x

    sigma_y2 = sum((ordinates[i] - a*abscissa[i] - b)**2 for i in range(n)) / (n - 2)
    sigma_a2 = sigma_y2 / (n * (x2 - x ** 2))
    sigma_b2 = (sigma_y2 * x2) / (n * (x2 - x ** 2))

    return LSMDescription(
        incline=a,
        shift=b,
        incline_error=sigma_a2**0.5,
        shift_error=sigma_b2**0.5
    )
