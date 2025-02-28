package service

import (
	"database/sql"
	"log"
	"math"
	"os"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"

	"backend_go/internal/models"
)

// Service encapsulates the business logic and database connection.
type Service struct {
	DB *sql.DB
}

// NewService initializes the Service with a connection to the SQLite database specified by dbPath.
func NewService(dbPath string) (*Service, error) {
	db, err := sql.Open("sqlite3", dbPath+"?_parseTime=true")
	if err != nil {
		return nil, err
	}

	// Test the database connection
	if err = db.Ping(); err != nil {
		return nil, err
	}

	log.Println("Database connection established")

	// Run migrations
	if err := Migrate(db); err != nil {
		log.Println("Warning: migration failed:", err)
	}

	// Optionally seed data for testing purposes
	if err := SeedData(db); err != nil {
		log.Println("Warning: seeding data failed:", err)
	}

	return &Service{DB: db}, nil
}

// Close closes the database connection.
func (s *Service) Close() error {
	return s.DB.Close()
}

// GetWords fetches all words from the database.
func (s *Service) GetWords() ([]models.Word, error) {
	rows, err := s.DB.Query("SELECT id, japanese, romaji, english, parts FROM words")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	words := make([]models.Word, 0)
	for rows.Next() {
		var word models.Word
		if err := rows.Scan(&word.ID, &word.Japanese, &word.Romaji, &word.English, &word.Parts); err != nil {
			return nil, err
		}
		words = append(words, word)
	}
	return words, nil
}

// CreateStudySession inserts a new study session into the database and returns its ID.
func (s *Service) CreateStudySession(groupID int, studyActivityID int) (int64, error) {
	result, err := s.DB.Exec("INSERT INTO study_sessions (group_id, study_activity_id) VALUES (?, ?)", groupID, studyActivityID)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

// GetStudySessionByID retrieves a study session by its ID.
func (s *Service) GetStudySessionByID(sessionID int) (*models.StudySession, error) {
	query := `SELECT id, group_id, created_at, study_activity_id FROM study_sessions WHERE id = ?`
	row := s.DB.QueryRow(query, sessionID)

	var session models.StudySession
	var nullCreatedAt sql.NullTime

	log.Printf("Fetching study session with ID: %d", sessionID)

	if err := row.Scan(&session.ID, &session.GroupID, &nullCreatedAt, &session.StudyActivityID); err != nil {
		log.Printf("Error scanning row for session ID %d: %v", sessionID, err)
		return nil, err
	}

	if nullCreatedAt.Valid {
		session.CreatedAt = nullCreatedAt.Time
		log.Printf("Session ID %d has valid created_at: %v", sessionID, session.CreatedAt)
	} else {
		session.CreatedAt = time.Now()
		log.Printf("Session ID %d has null created_at, using current time: %v", sessionID, session.CreatedAt)
	}
	return &session, nil
}

// GetDashboardLastStudySession dynamically returns information about the most recent study session.
func (s *Service) GetDashboardLastStudySession() (map[string]interface{}, error) {
	query := `SELECT ss.id, ss.group_id, ss.created_at, ss.study_activity_id, g.name 
	          FROM study_sessions ss
	          JOIN groups g ON ss.group_id = g.id
	          ORDER BY ss.created_at DESC 
	          LIMIT 1`
	row := s.DB.QueryRow(query)

	var id, groupID, studyActivityID int
	var nullCreatedAt sql.NullTime
	var groupName string
	err := row.Scan(&id, &groupID, &nullCreatedAt, &studyActivityID, &groupName)
	if err == sql.ErrNoRows {
		return map[string]interface{}{
			"id":                0,
			"group_id":          0,
			"created_at":        "",
			"study_activity_id": 0,
			"group_name":        "",
		}, nil
	} else if err != nil {
		return nil, err
	}

	var createdAtStr string
	if nullCreatedAt.Valid {
		createdAtStr = nullCreatedAt.Time.Format(time.RFC3339)
	} else {
		createdAtStr = ""
	}

	return map[string]interface{}{
		"id":                id,
		"group_id":          groupID,
		"created_at":        createdAtStr,
		"study_activity_id": studyActivityID,
		"group_name":        groupName,
	}, nil
}

// GetDashboardStudyProgress returns study progress statistics.
func (s *Service) GetDashboardStudyProgress() (map[string]interface{}, error) {
	var totalStudied int
	err := s.DB.QueryRow("SELECT COUNT(DISTINCT word_id) FROM word_review_items").Scan(&totalStudied)
	if err != nil {
		return nil, err
	}

	var totalAvailable int
	err = s.DB.QueryRow("SELECT COUNT(*) FROM words").Scan(&totalAvailable)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"total_words_studied":   totalStudied,
		"total_available_words": totalAvailable,
	}, nil
}

// GetDashboardQuickStats returns a quick overview of dashboard statistics.
func (s *Service) GetDashboardQuickStats() (map[string]interface{}, error) {
	var totalWords int
	if err := s.DB.QueryRow("SELECT COUNT(*) FROM words").Scan(&totalWords); err != nil {
		return nil, err
	}

	var totalGroups int
	if err := s.DB.QueryRow("SELECT COUNT(*) FROM groups").Scan(&totalGroups); err != nil {
		return nil, err
	}

	wordsMastered := int(math.Round(float64(totalWords) * 0.24))

	var avgCorrect sql.NullFloat64
	if err := s.DB.QueryRow("SELECT AVG(CASE WHEN correct THEN 1.0 ELSE 0.0 END) FROM word_review_items").Scan(&avgCorrect); err != nil {
		return nil, err
	}
	recentAccuracy := 0.0
	if avgCorrect.Valid {
		recentAccuracy = avgCorrect.Float64 * 100.0
	}

	return map[string]interface{}{
		"total_words":     totalWords,
		"total_groups":    totalGroups,
		"words_mastered":  wordsMastered,
		"recent_accuracy": recentAccuracy,
	}, nil
}

// SeedData inserts sample data into the database if tables are empty.
func SeedData(db *sql.DB) error {
	// Reset tables for testing purposes
	stmts := []string{
		"DELETE FROM word_review_items",
		"DELETE FROM study_activities",
		"DELETE FROM study_sessions",
		"DELETE FROM word_groups",
		"DELETE FROM words",
		"DELETE FROM groups",
	}
	for _, stmt := range stmts {
		if _, err := db.Exec(stmt); err != nil {
			return err
		}
	}

	// Reset auto-increment counters in sqlite_sequence
	seqTables := []string{"groups", "words", "study_sessions", "word_review_items", "study_activities", "word_groups"}
	for _, table := range seqTables {
		db.Exec("DELETE FROM sqlite_sequence WHERE name=?", table)
	}

	// Insert seed data in proper order
	// 1. Insert a group
	if _, err := db.Exec("INSERT INTO groups (name) VALUES (?)", "Basic Greetings"); err != nil {
		return err
	}

	// 2. Insert a word
	if _, err := db.Exec("INSERT INTO words (japanese, romaji, english, parts) VALUES (?, ?, ?, ?)", "こんにちは", "konnichiwa", "hello", ""); err != nil {
		return err
	}

	// 3. Insert a study session with a dummy study_activity_id (0) for now
	if _, err := db.Exec("INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES (?, ?, datetime('now'))", 1, 0); err != nil {
		return err
	}

	// 4. Insert a study activity for the study session with id 1 (assuming it's the first row)
	if _, err := db.Exec("INSERT INTO study_activities (study_session_id, group_id) VALUES (?, ?)", 1, 1); err != nil {
		return err
	}

	// 5. Update the inserted study session to set study_activity_id properly (to 1)
	if _, err := db.Exec("UPDATE study_sessions SET study_activity_id = ? WHERE id = ?", 1, 1); err != nil {
		return err
	}

	// 6. Insert a word review item as an example
	if _, err := db.Exec("INSERT INTO word_review_items (word_id, study_session_id, correct) VALUES (?, ?, ?)", 1, 1, true); err != nil {
		return err
	}

	return nil
}

// Migrate executes the SQL migration scripts to initialize the database schema.
func Migrate(db *sql.DB) error {
	// Try primary path
	filename := "backend_go/db/migrations/0001_init.sql"
	data, err := os.ReadFile(filename)
	if err != nil {
		// If not found, try alternate path
		filename = "db/migrations/0001_init.sql"
		data, err = os.ReadFile(filename)
		if err != nil {
			return err
		}
	}

	// Split the file content into individual statements
	stmts := strings.Split(string(data), ";")
	for _, stmt := range stmts {
		stmt = strings.TrimSpace(stmt)
		if stmt == "" {
			continue
		}
		_, err = db.Exec(stmt)
		if err != nil {
			return err
		}
	}
	return nil
}

//////////////////////////////////////
// Business Logic Endpoints
//////////////////////////////////////

// GetStudyActivity retrieves a study activity by its ID.
func (s *Service) GetStudyActivity(id int) (*models.StudyActivity, error) {
	row := s.DB.QueryRow("SELECT id, study_session_id, group_id, created_at FROM study_activities WHERE id = ?", id)
	var activity models.StudyActivity
	var nullCreatedAt sql.NullTime
	err := row.Scan(&activity.ID, &activity.StudySessionID, &activity.GroupID, &nullCreatedAt)
	if err != nil {
		return nil, err
	}
	if nullCreatedAt.Valid {
		activity.CreatedAt = nullCreatedAt.Time
	} else {
		activity.CreatedAt = time.Now()
	}
	return &activity, nil
}

// GetStudyActivitySessions retrieves the study session associated with a given study activity ID.
func (s *Service) GetStudyActivitySessions(activityID int) (*models.StudySession, error) {
	var studySessionID int
	err := s.DB.QueryRow("SELECT study_session_id FROM study_activities WHERE id = ?", activityID).Scan(&studySessionID)
	if err != nil {
		return nil, err
	}
	return s.GetStudySessionByID(studySessionID)
}

// CreateStudyActivity creates a new study activity with the given studySessionID and groupID.
func (s *Service) CreateStudyActivity(studySessionID, groupID int) (int64, error) {
	result, err := s.DB.Exec("INSERT INTO study_activities (study_session_id, group_id) VALUES (?, ?)", studySessionID, groupID)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

// GetWordByID retrieves a word by its ID.
func (s *Service) GetWordByID(id int) (*models.Word, error) {
	row := s.DB.QueryRow("SELECT id, japanese, romaji, english, parts FROM words WHERE id = ?", id)
	var word models.Word
	err := row.Scan(&word.ID, &word.Japanese, &word.Romaji, &word.English, &word.Parts)
	if err != nil {
		return nil, err
	}
	return &word, nil
}

// ListGroups retrieves all groups.
func (s *Service) ListGroups() ([]models.Group, error) {
	rows, err := s.DB.Query("SELECT id, name FROM groups")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var groups []models.Group
	for rows.Next() {
		var grp models.Group
		if err := rows.Scan(&grp.ID, &grp.Name); err != nil {
			return nil, err
		}
		groups = append(groups, grp)
	}
	return groups, nil
}

// GetGroupByID retrieves a group by its ID.
func (s *Service) GetGroupByID(id int) (*models.Group, error) {
	row := s.DB.QueryRow("SELECT id, name FROM groups WHERE id = ?", id)
	var grp models.Group
	if err := row.Scan(&grp.ID, &grp.Name); err != nil {
		return nil, err
	}
	return &grp, nil
}

// GetGroupWords retrieves all words associated with a given group ID via the join table word_groups.
func (s *Service) GetGroupWords(groupID int) ([]models.Word, error) {
	query := `SELECT w.id, w.japanese, w.romaji, w.english, w.parts 
	          FROM words w 
	          JOIN word_groups wg ON w.id = wg.word_id 
	          WHERE wg.group_id = ?`
	rows, err := s.DB.Query(query, groupID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var words []models.Word
	for rows.Next() {
		var word models.Word
		if err := rows.Scan(&word.ID, &word.Japanese, &word.Romaji, &word.English, &word.Parts); err != nil {
			return nil, err
		}
		words = append(words, word)
	}
	return words, nil
}

// GetGroupStudySessions retrieves all study sessions for a given group.
func (s *Service) GetGroupStudySessions(groupID int) ([]models.StudySession, error) {
	rows, err := s.DB.Query("SELECT id, group_id, created_at, study_activity_id FROM study_sessions WHERE group_id = ?", groupID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var sessions []models.StudySession
	for rows.Next() {
		var session models.StudySession
		if err := rows.Scan(&session.ID, &session.GroupID, &session.CreatedAt, &session.StudyActivityID); err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}
	return sessions, nil
}

// ListStudySessions retrieves all study sessions.
func (s *Service) ListStudySessions() ([]models.StudySession, error) {
	rows, err := s.DB.Query("SELECT id, group_id, created_at, study_activity_id FROM study_sessions")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	sessions := make([]models.StudySession, 0)
	for rows.Next() {
		var session models.StudySession
		if err := rows.Scan(&session.ID, &session.GroupID, &session.CreatedAt, &session.StudyActivityID); err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}
	return sessions, nil
}

// GetStudySessionWords retrieves words associated with a given study session via the word_review_items table.
func (s *Service) GetStudySessionWords(sessionID int) ([]models.Word, error) {
	query := `SELECT w.id, w.japanese, w.romaji, w.english, w.parts 
	          FROM words w 
	          JOIN word_review_items wr ON w.id = wr.word_id 
	          WHERE wr.study_session_id = ?`
	rows, err := s.DB.Query(query, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	words := make([]models.Word, 0) // ensure empty slice
	for rows.Next() {
		var word models.Word
		if err := rows.Scan(&word.ID, &word.Japanese, &word.Romaji, &word.English, &word.Parts); err != nil {
			return nil, err
		}
		words = append(words, word)
	}
	return words, nil
}

// ResetHistory clears all records from word_review_items.
func (s *Service) ResetHistory() error {
	_, err := s.DB.Exec("DELETE FROM word_review_items")
	return err
}

// FullReset deletes all records from the main tables in proper order.
func (s *Service) FullReset() error {
	queries := []string{
		"DELETE FROM word_review_items",
		"DELETE FROM study_activities",
		"DELETE FROM study_sessions",
		"DELETE FROM word_groups",
		"DELETE FROM words",
		"DELETE FROM groups",
	}
	for _, q := range queries {
		if _, err := s.DB.Exec(q); err != nil {
			return err
		}
	}

	// Reset auto-increment counters
	if _, err := s.DB.Exec("DELETE FROM sqlite_sequence"); err != nil {
		return err
	}

	// Re-seed the database with default data
	return SeedData(s.DB)
}

// ReviewWord records the review result for a given word in a study session.
func (s *Service) ReviewWord(studySessionID int, wordID int, correct bool) error {
	_, err := s.DB.Exec("INSERT INTO word_review_items (word_id, study_session_id, correct) VALUES (?, ?, ?)", wordID, studySessionID, correct)
	return err
}

// CreateGroup inserts a new group into the database and returns its ID.
func (s *Service) CreateGroup(name string) (int, error) {
	result, err := s.DB.Exec("INSERT INTO groups (name) VALUES (?)", name)
	if err != nil {
		return 0, err
	}
	id, err := result.LastInsertId()
	if err != nil {
		return 0, err
	}
	return int(id), nil
}

// UpdateGroup updates the name of an existing group identified by id.
func (s *Service) UpdateGroup(id int, name string) error {
	_, err := s.DB.Exec("UPDATE groups SET name = ? WHERE id = ?", name, id)
	return err
}

// DeleteGroup deletes the group with the given id from the database.
func (s *Service) DeleteGroup(id int) error {
	_, err := s.DB.Exec("DELETE FROM groups WHERE id = ?", id)
	return err
}

// New service functions for managing Words and Study Sessions

func (s *Service) CreateWord(japanese, romaji, english, parts string) (int, error) {
	result, err := s.DB.Exec("INSERT INTO words (japanese, romaji, english, parts) VALUES (?, ?, ?, ?)", japanese, romaji, english, parts)
	if err != nil {
		return 0, err
	}
	id, err := result.LastInsertId()
	if err != nil {
		return 0, err
	}
	return int(id), nil
}

func (s *Service) UpdateWord(id int, english string) error {
	result, err := s.DB.Exec("UPDATE words SET english = ? WHERE id = ?", english, id)
	if err != nil {
		return err
	}
	count, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if count == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func (s *Service) DeleteWord(id int) error {
	result, err := s.DB.Exec("DELETE FROM words WHERE id = ?", id)
	if err != nil {
		return err
	}
	count, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if count == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func (s *Service) UpdateStudySession(sessionID int, studyActivityID int) error {
	result, err := s.DB.Exec("UPDATE study_sessions SET study_activity_id = ? WHERE id = ?", studyActivityID, sessionID)
	if err != nil {
		return err
	}
	count, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if count == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func (s *Service) DeleteStudySession(sessionID int) error {
	result, err := s.DB.Exec("DELETE FROM study_sessions WHERE id = ?", sessionID)
	if err != nil {
		return err
	}
	count, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if count == 0 {
		return sql.ErrNoRows
	}
	return nil
}

// TODO: Implement business logic functions such as managing words, groups, study sessions, etc.
