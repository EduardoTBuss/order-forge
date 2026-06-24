"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  useCallback,
  useEffect,
  useState,
} from "react";

interface LoadingScreenProps {
  isLoading: boolean;
  minimumDisplayTime?: number;
}

const WORDS = ["MACHINES", "LIKE", "ME"];
const TYPING_SPEED = 60; // ms per character
const WORD_DELAY = 100; // ms delay between words
const CURSOR_BLINK_SPEED = 530; // ms

export function LoadingScreen({
  isLoading,
  minimumDisplayTime = 800,
}: LoadingScreenProps): ReactNode {
  const [shouldShow, setShouldShow] = useState(false);
  const [displayedText, setDisplayedText] = useState<string[]>(["", "", ""]);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const [isTypingComplete, setIsTypingComplete] = useState(false);
  const [showCursor, setShowCursor] = useState(true);

  // Handle minimum display time
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (isLoading) {
      setShouldShow(true);
      // Reset typing state when loading starts
      setDisplayedText(["", "", ""]);
      setCurrentWordIndex(0);
      setCurrentCharIndex(0);
      setIsTypingComplete(false);
    } else if (shouldShow) {
      // Ensure minimum display time before hiding
      timeoutId = setTimeout(() => {
        setShouldShow(false);
      }, minimumDisplayTime);
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isLoading, minimumDisplayTime, shouldShow]);

  // Typing animation
  useEffect(() => {
    if (!shouldShow || isTypingComplete) return;

    const currentWord = WORDS[currentWordIndex];

    if (currentCharIndex < currentWord.length) {
      const typingTimeout = setTimeout(() => {
        setDisplayedText((prev) => {
          const newText = [...prev];
          newText[currentWordIndex] = currentWord.slice(
            0,
            currentCharIndex + 1,
          );
          return newText;
        });
        setCurrentCharIndex((prev) => prev + 1);
      }, TYPING_SPEED);

      return () => clearTimeout(typingTimeout);
    } else if (currentWordIndex < WORDS.length - 1) {
      // Move to next word
      const wordDelayTimeout = setTimeout(() => {
        setCurrentWordIndex((prev) => prev + 1);
        setCurrentCharIndex(0);
      }, WORD_DELAY);

      return () => clearTimeout(wordDelayTimeout);
    } else {
      // All words typed
      setIsTypingComplete(true);
    }
  }, [shouldShow, currentWordIndex, currentCharIndex, isTypingComplete]);

  // Cursor blink
  useEffect(() => {
    if (!shouldShow) return;

    const blinkInterval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, CURSOR_BLINK_SPEED);

    return () => clearInterval(blinkInterval);
  }, [shouldShow]);

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="fixed inset-0 z-[9999] flex items-center justify-center"
          style={{
            background:
              "linear-gradient(135deg, #0a0a0a 0%, #0f172a 50%, #020617 100%)",
          }}
        >
          {/* Subtle animated background gradient */}
          <div
            className="absolute inset-0 opacity-30"
            style={{
              background:
                "radial-gradient(ellipse at 30% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)",
            }}
          />

          {/* Content container */}
          <div className="relative flex flex-col items-start">
            {/* Logo text with typing animation */}
            <div className="flex flex-col font-bold tracking-tight">
              {WORDS.map((word, index) => (
                <motion.div
                  key={word}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{
                    opacity: displayedText[index] ? 1 : 0.3,
                    x: 0,
                  }}
                  transition={{
                    duration: 0.2,
                    delay: index * 0.1,
                    ease: [0.22, 1, 0.36, 1],
                  }}
                  className="relative"
                >
                  <span
                    className="select-none text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-7xl"
                    style={{
                      letterSpacing: "-0.02em",
                      lineHeight: 1.05,
                    }}
                  >
                    {displayedText[index]}
                    {/* Cursor - only show on the current word being typed */}
                    {currentWordIndex === index && !isTypingComplete && (
                      <span
                        className={`ml-[2px] inline-block h-[1em] w-[3px] align-baseline transition-opacity duration-100 sm:w-[4px] ${
                          showCursor ? "opacity-100" : "opacity-0"
                        }`}
                        style={{
                          background:
                            "linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%)",
                          marginBottom: "0.1em",
                        }}
                      />
                    )}
                    {/* Placeholder to maintain width */}
                    <span className="opacity-0 absolute left-0">{word}</span>
                  </span>
                </motion.div>
              ))}
            </div>

            {/* Loading indicator */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.4 }}
              className="mt-8 flex items-center gap-3"
            >
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-white/60"
                    animate={{
                      scale: [1, 1.5, 1],
                      opacity: [0.4, 1, 0.4],
                    }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      delay: i * 0.2,
                      ease: "easeInOut",
                    }}
                  />
                ))}
              </div>
            </motion.div>
          </div>

          {/* Corner accent */}
          <div
            className="pointer-events-none absolute bottom-0 right-0 h-1/3 w-1/3 opacity-20"
            style={{
              background:
                "radial-gradient(ellipse at bottom right, rgba(59, 130, 246, 0.3) 0%, transparent 70%)",
            }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export interface UseLoadingScreenResult {
  isLoading: boolean;
  showLoading: () => void;
  hideLoading: () => void;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
}

// Export a hook for programmatic control
export function useLoadingScreen(): UseLoadingScreenResult {
  const [isLoading, setIsLoading] = useState(false);

  const showLoading = useCallback(() => setIsLoading(true), []);
  const hideLoading = useCallback(() => setIsLoading(false), []);

  return { isLoading, showLoading, hideLoading, setIsLoading };
}
