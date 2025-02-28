import { NextResponse } from 'next/server';

// Define the expected structure of vocabulary items
interface VocabularyItem {
  kanji: string;
  romaji: string;
  english: string;
  parts: {
    kanji: string;
    romaji: string[];
  }[];
}

// Common Japanese words that can be used as fallbacks for various themes
const COMMON_JAPANESE_WORDS = [
  { kanji: "言葉", romaji: "kotoba", english: "word", parts: [{ kanji: "言", romaji: ["koto"] }, { kanji: "葉", romaji: ["ha", "ba"] }] },
  { kanji: "日本", romaji: "nihon", english: "Japan", parts: [{ kanji: "日", romaji: ["ni", "hi"] }, { kanji: "本", romaji: ["hon"] }] },
  { kanji: "勉強", romaji: "benkyou", english: "study", parts: [{ kanji: "勉", romaji: ["ben"] }, { kanji: "強", romaji: ["kyou"] }] },
  { kanji: "文化", romaji: "bunka", english: "culture", parts: [{ kanji: "文", romaji: ["bun"] }, { kanji: "化", romaji: ["ka"] }] },
  { kanji: "生活", romaji: "seikatsu", english: "life", parts: [{ kanji: "生", romaji: ["sei"] }, { kanji: "活", romaji: ["katsu"] }] }
];

// This ensures the route is always dynamic
export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { theme } = body;

    if (!theme) {
      return NextResponse.json(
        { error: 'Theme is required' },
        { status: 400 }
      );
    }

    // Prepare the prompt for Groq with explicit formatting instructions
    const prompt = `Generate a structured vocabulary list for the theme: "${theme}" in Japanese.

Your response must be ONLY a valid JSON array with exactly this structure:
[
  {
    "kanji": "日本語",
    "romaji": "nihongo",
    "english": "Japanese language",
    "parts": [
      {
        "kanji": "日本",
        "romaji": ["nihon"]
      },
      {
        "kanji": "語",
        "romaji": ["go"]
      }
    ]
  }
]

CRITICAL REQUIREMENTS:
- Include exactly 5 vocabulary items related to the theme.
- Every item MUST have actual Japanese kanji characters in the "kanji" field.
- NEVER use English words, placeholders, or brackets in the kanji field.
- If you cannot find exact matches for the theme, use related Japanese concepts.
- For example, if the theme is "computer science" and you don't know specific terms, use general technology terms in Japanese.
- ALWAYS break down each vocabulary item into its component parts in the "parts" array.
- For each part, include the kanji character(s) and its romaji reading(s).
- The parts should represent the meaningful components of the word (not just individual characters).
- Return ONLY the JSON array with no additional text.
- Ensure all JSON is valid with no syntax errors.`;

    // Call Groq API
    const apiKey = process.env.GROQ_API_KEY || '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';
    
    try {
      const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: 'llama3-8b-8192',
          messages: [
            {
              role: 'system',
              content: 'You are a Japanese language expert that outputs only valid, properly formatted JSON arrays with Japanese vocabulary. Every vocabulary item must include proper Japanese kanji, romaji pronunciation, English translation, and a breakdown of its component parts. NEVER use placeholders, English words, or brackets in the kanji field. If you cannot provide proper kanji for a concept, use a related Japanese word instead. Always break down each word into its meaningful parts with accurate romaji readings.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          temperature: 0.1, // Very low temperature for consistent formatting
          max_tokens: 2000
        })
      });

      // Check if the response is OK
      if (!response.ok) {
        // Try to parse the error response as JSON
        let errorMessage = 'Failed to generate vocabulary';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error?.message || 'Unknown API error';
        } catch (parseError) {
          // If we can't parse the response as JSON, get the text
          try {
            const errorText = await response.text();
            errorMessage = `API error: ${response.status} - ${errorText.substring(0, 100)}...`;
          } catch (textError) {
            errorMessage = `API error: ${response.status}`;
          }
        }
        
        console.error('Groq API error:', errorMessage);
        return NextResponse.json({ error: errorMessage }, { status: 500 });
      }

      // Parse the successful response
      const data = await response.json();
      
      // Extract the generated content
      const generatedContent = data.choices[0].message.content;
      
      // Clean the content before attempting to parse
      const cleanContent = (text: string): string => {
        return text
          .replace(/```json/gi, '') // Remove json code block markers
          .replace(/```/g, '')      // Remove any remaining code block markers
          .replace(/^\s*[\r\n]+/gm, '') // Remove empty lines
          .replace(/^[^[]*/, '')    // Remove any text before the first [
          .replace(/][^]*$/, ']')   // Remove any text after the last ]
          .trim();
      };
      
      // Function to manually fix common JSON syntax errors
      const fixJsonSyntax = (text: string): string => {
        return text
          .replace(/"kanji"\s*:\s*,/g, '"kanji": "",')  // Fix empty kanji values
          .replace(/"romaji"\s*:\s*,/g, '"romaji": "",') // Fix empty romaji values
          .replace(/"english"\s*:\s*,/g, '"english": "",') // Fix empty english values
          .replace(/,\s*}/g, '}')   // Remove trailing commas in objects
          .replace(/,\s*]/g, ']')   // Remove trailing commas in arrays
          .replace(/}\s*{/g, '},{') // Add commas between objects
          .replace(/]\s*\[/g, '],[') // Add commas between arrays
          .replace(/"\s*"/g, '","') // Add commas between strings
          .replace(/:\s*"/g, ':"')  // Fix spacing in key-value pairs
          .replace(/"\s*:/g, '":')  // Fix spacing in key-value pairs
          .replace(/\\/g, '\\\\');  // Escape backslashes
      };
      
      // Try to parse the JSON with multiple fallback strategies
      let vocabularyData: VocabularyItem[] = [];
      let parseSuccess = false;
      
      // First attempt: Try to parse the raw content
      try {
        vocabularyData = JSON.parse(generatedContent);
        if (Array.isArray(vocabularyData)) {
          parseSuccess = true;
        }
      } catch (e) {
        console.log('First parse attempt failed, trying cleaned content');
      }
      
      // Second attempt: Try with cleaned content
      if (!parseSuccess) {
        const cleaned = cleanContent(generatedContent);
        try {
          vocabularyData = JSON.parse(cleaned);
          if (Array.isArray(vocabularyData)) {
            parseSuccess = true;
          }
        } catch (e) {
          console.log('Second parse attempt failed, trying with syntax fixes');
        }
      }
      
      // Third attempt: Try with syntax fixes
      if (!parseSuccess) {
        const fixed = fixJsonSyntax(cleanContent(generatedContent));
        try {
          vocabularyData = JSON.parse(fixed);
          if (Array.isArray(vocabularyData)) {
            parseSuccess = true;
          }
        } catch (e) {
          console.error('All JSON parsing attempts failed');
        }
      }
      
      // If all parsing attempts failed, return an error
      if (!parseSuccess) {
        return NextResponse.json(
          { 
            error: 'Failed to parse vocabulary data: Invalid JSON format',
            // Include a sanitized version of the response for debugging
            rawResponse: generatedContent
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .substring(0, 200) + '...'
          },
          { status: 500 }
        );
      }
      
      // Check if we have valid kanji in each item
      const hasValidKanji = (text: string): boolean => {
        // Check if the string contains at least one Japanese character
        // Japanese character Unicode ranges:
        // Hiragana: \u3040-\u309F
        // Katakana: \u30A0-\u30FF
        // Kanji: \u4E00-\u9FAF
        return /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(text);
      };
      
      // Check for placeholder patterns
      const isPlaceholder = (text: string): boolean => {
        // Check for common placeholder patterns
        return (
          text.startsWith('[') && text.endsWith(']') || // [Placeholder]
          /Item \d+/.test(text) ||                     // Item 1, Item 2, etc.
          /^[a-zA-Z\s]+$/.test(text) ||                // English-only text
          text.includes('placeholder') ||              // Contains "placeholder"
          text.includes('example')                     // Contains "example"
        );
      };
      
      // Function to generate parts for a kanji word if missing
      const generatePartsIfMissing = (item: VocabularyItem): VocabularyItem => {
        // If parts array is empty or undefined, generate parts
        if (!item.parts || item.parts.length === 0) {
          const parts = [];
          
          // For single character kanji, just use the whole character as a part
          if (item.kanji.length === 1) {
            parts.push({
              kanji: item.kanji,
              romaji: [item.romaji]
            });
          } 
          // For multi-character kanji, try to break it down
          else {
            // Simple approach: treat each character as a part
            // In a real app, we would use a dictionary to get proper readings
            for (let i = 0; i < item.kanji.length; i++) {
              const char = item.kanji.charAt(i);
              
              // Skip non-kanji characters
              if (!hasValidKanji(char)) continue;
              
              // Create a part with the character
              // For romaji, we'll use a placeholder since we don't know the exact reading
              parts.push({
                kanji: char,
                romaji: ["?"] // Indicate we don't know the exact reading
              });
            }
            
            // If we couldn't break it down, use the whole word
            if (parts.length === 0) {
              parts.push({
                kanji: item.kanji,
                romaji: [item.romaji]
              });
            }
          }
          
          return {
            ...item,
            parts
          };
        }
        
        return item;
      };
      
      // Validate and sanitize the data structure
      const sanitizedData = vocabularyData.map((item) => {
        // Create a valid item with default values for missing fields
        const sanitizedItem: VocabularyItem = {
          kanji: item.kanji || "",
          romaji: item.romaji || "",
          english: item.english || "",
          parts: Array.isArray(item.parts) ? item.parts.map(part => ({
            kanji: part.kanji || "",
            romaji: Array.isArray(part.romaji) ? part.romaji : [part.romaji || ""]
          })) : []
        };
        
        // Generate parts if missing
        return generatePartsIfMissing(sanitizedItem);
      });
      
      // Filter out items with invalid kanji
      const validItems = sanitizedData.filter(item => 
        hasValidKanji(item.kanji) && !isPlaceholder(item.kanji)
      );
      
      // If we don't have enough valid items, make a second API call with a more specific prompt
      if (validItems.length < 5) {
        console.log(`Only ${validItems.length} valid items found, making a second attempt`);
        
        // Create a more specific prompt for the second attempt
        const secondAttemptPrompt = `Generate a structured vocabulary list for the theme: "${theme}" in Japanese.

Your response must be ONLY a valid JSON array with exactly this structure:
[
  {
    "kanji": "日本語",
    "romaji": "nihongo",
    "english": "Japanese language",
    "parts": [
      {
        "kanji": "日本",
        "romaji": ["nihon"]
      },
      {
        "kanji": "語",
        "romaji": ["go"]
      }
    ]
  }
]

ULTRA CRITICAL REQUIREMENTS:
- Include exactly 5 vocabulary items related to the theme.
- Every item MUST have actual Japanese kanji characters in the "kanji" field.
- NEVER use English words, placeholders, or brackets in the kanji field.
- If you cannot find exact matches for the theme, use related Japanese concepts or common Japanese words.
- ALWAYS include a detailed breakdown of each word's parts in the "parts" array.
- Each part should include the kanji component and its romaji reading(s).
- Return ONLY the JSON array with no additional text.
- This is your final chance to provide proper Japanese kanji - it's absolutely essential.`;

        // Make a second API call with a more specific prompt
        const secondResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          },
          body: JSON.stringify({
            model: 'llama3-8b-8192',
            messages: [
              {
                role: 'system',
                content: 'You are a Japanese language expert. You must ONLY output valid JSON with proper Japanese kanji characters. Never use English or placeholders in the kanji field. If you cannot provide specific vocabulary for the theme, use common Japanese words instead. Always break down each word into its component parts with accurate romaji readings.'
              },
              {
                role: 'user',
                content: secondAttemptPrompt
              }
            ],
            temperature: 0.05, // Extremely low temperature for consistent results
            max_tokens: 2000
          })
        });

        if (secondResponse.ok) {
          const secondData = await secondResponse.json();
          const secondContent = secondData.choices[0].message.content;
          
          try {
            // Try to parse the second response
            let secondVocabularyData: VocabularyItem[] = [];
            let secondParseSuccess = false;
            
            // Try different parsing strategies as before
            try {
              secondVocabularyData = JSON.parse(secondContent);
              if (Array.isArray(secondVocabularyData)) {
                secondParseSuccess = true;
              }
            } catch (e) {
              const cleaned = cleanContent(secondContent);
              try {
                secondVocabularyData = JSON.parse(cleaned);
                if (Array.isArray(secondVocabularyData)) {
                  secondParseSuccess = true;
                }
              } catch (e) {
                const fixed = fixJsonSyntax(cleanContent(secondContent));
                try {
                  secondVocabularyData = JSON.parse(fixed);
                  if (Array.isArray(secondVocabularyData)) {
                    secondParseSuccess = true;
                  }
                } catch (e) {
                  console.error('All JSON parsing attempts failed for second attempt');
                }
              }
            }
            
            if (secondParseSuccess) {
              // Validate and sanitize the second attempt data
              const secondSanitizedData = secondVocabularyData.map((item) => {
                const sanitizedItem = {
                  kanji: item.kanji || "",
                  romaji: item.romaji || "",
                  english: item.english || "",
                  parts: Array.isArray(item.parts) ? item.parts.map(part => ({
                    kanji: part.kanji || "",
                    romaji: Array.isArray(part.romaji) ? part.romaji : [part.romaji || ""]
                  })) : []
                };
                
                // Generate parts if missing
                return generatePartsIfMissing(sanitizedItem);
              });
              
              // Filter valid items from the second attempt
              const secondValidItems = secondSanitizedData.filter(item => 
                hasValidKanji(item.kanji) && !isPlaceholder(item.kanji)
              );
              
              // If the second attempt has valid items, use those
              if (secondValidItems.length > 0) {
                // Combine the valid items from both attempts, prioritizing the second attempt
                const combinedItems = [...secondValidItems];
                
                // Add items from the first attempt if needed to reach 5 items
                if (combinedItems.length < 5 && validItems.length > 0) {
                  // Add items from the first attempt that aren't duplicates
                  for (const item of validItems) {
                    if (combinedItems.length >= 5) break;
                    
                    // Check if this item is already in the combined list
                    const isDuplicate = combinedItems.some(
                      existingItem => existingItem.kanji === item.kanji
                    );
                    
                    if (!isDuplicate) {
                      combinedItems.push(item);
                    }
                  }
                }
                
                // If we have at least one valid item, return it
                if (combinedItems.length > 0) {
                  return NextResponse.json({ vocabulary: combinedItems });
                }
              }
            }
          } catch (secondError) {
            console.error('Error processing second attempt:', secondError);
          }
        }
      }
      
      // If we still don't have valid items after two attempts, use fallback common Japanese words
      if (validItems.length === 0) {
        console.log('No valid items found after two attempts, using fallback common Japanese words');
        
        // Create a set of fallback items with the theme as the English translation
        const fallbackItems = COMMON_JAPANESE_WORDS.map(word => ({
          ...word,
          english: `${word.english} (related to ${theme})` // Add context to the English translation
        }));
        
        return NextResponse.json({ 
          vocabulary: fallbackItems,
          message: "Could not generate specific vocabulary for this theme. Showing common Japanese words instead."
        });
      }
      
      // Return the best data we have
      return NextResponse.json({ vocabulary: validItems });
    } catch (fetchError) {
      console.error('Fetch error:', fetchError);
      const errorMessage = fetchError instanceof Error 
        ? fetchError.message 
        : 'Failed to connect to the Groq API';
      return NextResponse.json({ error: errorMessage }, { status: 500 });
    }
  } catch (error) {
    console.error('Error generating vocabulary:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return NextResponse.json(
      { error: `Failed to process request: ${errorMessage}` },
      { status: 500 }
    );
  }
}