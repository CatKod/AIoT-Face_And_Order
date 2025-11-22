/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body - Tich hop RC522 High Level
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "spi.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h> // Thu vien cho printf
#include "Timer.h"
#include "MFRC522_STM32.h" // Thu vien ban dang dung
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
extern timer_Objt Tim_1ms[MaxTIMER];

// --- KHAI BAO CHO RC522 ---
uint8_t uid[4]; // Mang luu ID the doc duoc

// Cau hinh struct dua tren so do chan (Pinout) trong anh ban gui:
// SPI: hspi1
// CS (SDA): PA4
// RESET: PB0
MFRC522_t rfID = {&hspi1, GPIOA, GPIO_PIN_4, GPIOB, GPIO_PIN_0};

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

// Ham nay giup printf() day du lieu ra cong UART1
int _write(int fd, unsigned char *buf, int len) {
  if (fd == 1 || fd == 2) {
    HAL_UART_Transmit(&huart1, buf, len, 1000);
  }
  return len;
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM2_Init();
  MX_SPI1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */

  // Khoi dong Timer ngat (cho logic cu cua ban)
  HAL_TIM_Base_Start_IT(&htim2);
  startTim(&Tim_1ms[0], 1000);

  // --- KHOI TAO RC522 ---
  // Truyen dia chi bien struct da khai bao o tren
  MFRC522_Init(&rfID);

  printf("System Init Done. Waiting for Card...\n");

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    // --- LOGIC 1: QUET THE RFID (High Level) ---
    // 1. Cho den khi co the quet
    if (waitcardDetect(&rfID) == STATUS_OK) {

      // 2. Doc UID cua the
      if (MFRC522_ReadUid(&rfID, uid) == STATUS_OK) {

        // In ID ra man hinh Serial
        printf("CARD ID: %02X %02X %02X %02X\n", uid[0], uid[1], uid[2], uid[3]);

        // Vi du 1: The Master -> Bat den Xanh (PA8)
        if ((uid[0] == 0x20) && (uid[1] == 0x00) && (uid[2] == 0x01) && (uid[3] == 0xE4)) {
            printf("Access Granted - GREEN LED ON\n");
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);   // Bat LED PA8
            HAL_Delay(1000);
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_RESET); // Tat LED PA8
        }
        // Vi du 2: The khac -> Bat den Do (PB15)
        else if ((uid[0] == 0x1D) && (uid[1] == 0x7D) && (uid[2] == 0xCD) && (uid[3] == 0x73)) {
            printf("Access Denied - RED LED ON\n");
            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_15, GPIO_PIN_SET);  // Bat LED PB15
            HAL_Delay(1000);
            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_15, GPIO_PIN_RESET);// Tat LED PB15
        }
        else {
            // The la -> Nhay den PC13 (Onboard)
            HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
            HAL_Delay(200);
            HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
        }
      }

      // 4. Doi nhat the ra moi tiep tuc
      waitcardRemoval(&rfID);
    }

    // --- LOGIC 2: TIMER CUA BAN ---
    scanTimer();
    if(Tim_1ms[0].En && Tim_1ms[0].Output){
        Tim_1ms[0].Output = 0;
        // Chi blink LED PC13 neu khong dang xu ly the
        // HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
