package models

import (
	"database/sql"
	"time"
)

// Word represents a vocabulary word.
type Word struct {
	ID       int            `json:"id"`
	Japanese string         `json:"japanese"`
	Romaji   string         `json:"romaji"`
	English  string         `json:"english"`
	Parts    sql.NullString `json:"parts,omitempty"`
}

// Group represents a thematic group of words.
type Group struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

// WordGroup represents the many-to-many relationship between words and groups.
type WordGroup struct {
	ID      int `json:"id"`
	WordID  int `json:"word_id"`
	GroupID int `json:"group_id"`
}

// StudySession represents a record of a study session.
type StudySession struct {
	ID              int       `json:"id"`
	GroupID         int       `json:"group_id"`
	CreatedAt       time.Time `json:"created_at"`
	StudyActivityID int       `json:"study_activity_id"`
}

// StudyActivity represents a specific study activity linked to a study session.
type StudyActivity struct {
	ID             int       `json:"id"`
	StudySessionID int       `json:"study_session_id"`
	GroupID        int       `json:"group_id"`
	CreatedAt      time.Time `json:"created_at"`
}

// WordReviewItem represents the review result of a word in a study session.
type WordReviewItem struct {
	WordID         int       `json:"word_id"`
	StudySessionID int       `json:"study_session_id"`
	Correct        bool      `json:"correct"`
	CreatedAt      time.Time `json:"created_at"`
}
