package handlers

import (
	"database/sql"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/gin-contrib/cors"

	"backend_go/internal/service"
)

var svc *service.Service

// RegisterRoutes registers API routes and their handlers, and accepts a service instance.
func RegisterRoutes(router *gin.Engine, serviceInstance *service.Service) {
	// Add recovery middleware to catch panics and prevent ECONNRESET errors
	router.Use(gin.Recovery())
	
	// Configure CORS
	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173"}, // Vite default port
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * 60 * 60, // 12 hours
	}))
	
	svc = serviceInstance
	api := router.Group("/api")
	{
		// Dashboard endpoints registered directly on the API group
		api.GET("/dashboard/last-study-session", GetLastStudySession)
		api.GET("/dashboard/study-progress", GetStudyProgress)
		api.GET("/dashboard/quick-stats", GetQuickStats)

		// Study Activities endpoints
		api.GET("/study_activities/:id", GetStudyActivity)
		api.GET("/study_activities/:id/study_sessions", GetStudyActivitySessions)
		api.POST("/study_activities", CreateStudyActivity)

		// Words endpoints
		api.GET("/words", ListWords)
		api.GET("/words/:id", GetWord)
		api.POST("/words", CreateWord)
		api.PUT("/words/:id", UpdateWord)
		api.DELETE("/words/:id", DeleteWord)

		// Groups endpoints
		api.GET("/groups", ListGroups)
		api.GET("/groups/:id", GetGroup)
		api.POST("/groups", CreateGroup)
		api.PUT("/groups/:id", UpdateGroup)
		api.DELETE("/groups/:id", DeleteGroup)
		api.GET("/groups/:id/words", GetGroupWords)
		api.GET("/groups/:id/study_sessions", GetGroupStudySessions)

		// Study Sessions endpoints
		api.POST("/study_sessions", CreateStudySession)
		api.GET("/study_sessions", ListStudySessions)
		api.GET("/study_sessions/:id", GetStudySession)
		api.GET("/study_sessions/:id/words", GetStudySessionWords)
		api.PUT("/study_sessions/:id", UpdateStudySession)
		api.DELETE("/study_sessions/:id", DeleteStudySession)

		// Reset endpoints
		api.POST("/reset_history", ResetHistory)
		api.POST("/full_reset", FullReset)

		// Word review endpoint
		api.POST("/study_sessions/:id/words/:word_id/review", ReviewWord)
	}
}

// Dashboard Handlers
func GetLastStudySession(c *gin.Context) {
	log.Println("[DEBUG] Handling GET /api/dashboard/last-study-session")
	data, err := svc.GetDashboardLastStudySession()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch last study session"})
		return
	}
	c.JSON(http.StatusOK, data)
}

func GetStudyProgress(c *gin.Context) {
	log.Println("[DEBUG] Handling GET /api/dashboard/study-progress")
	data, err := svc.GetDashboardStudyProgress()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch study progress"})
		return
	}
	c.JSON(http.StatusOK, data)
}

func GetQuickStats(c *gin.Context) {
	log.Println("[DEBUG] Handling GET /api/dashboard/quick-stats")
	data, err := svc.GetDashboardQuickStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch quick stats"})
		return
	}
	c.JSON(http.StatusOK, data)
}

// Study Activities Handlers
func GetStudyActivity(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study activity ID"})
		return
	}
	activity, err := svc.GetStudyActivity(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch study activity"})
		return
	}
	c.JSON(http.StatusOK, activity)
}

func GetStudyActivitySessions(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study activity ID"})
		return
	}
	session, err := svc.GetStudyActivitySessions(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch study activity sessions"})
		return
	}
	c.JSON(http.StatusOK, session)
}

func CreateStudyActivity(c *gin.Context) {
	var req struct {
		StudySessionID int `json:"study_session_id"`
		GroupID        int `json:"group_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	id, err := svc.CreateStudyActivity(req.StudySessionID, req.GroupID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create study activity"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"id": id})
}

// Words Handlers
func ListWords(c *gin.Context) {
	words, err := svc.GetWords()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch words"})
		return
	}
	c.JSON(http.StatusOK, words)
}

func GetWord(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid word ID"})
		return
	}
	word, err := svc.GetWordByID(id)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "Word not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch word"})
		}
		return
	}
	c.JSON(http.StatusOK, word)
}

// Groups Handlers
func ListGroups(c *gin.Context) {
	groups, err := svc.ListGroups()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list groups"})
		return
	}
	c.JSON(http.StatusOK, groups)
}

func GetGroup(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group ID"})
		return
	}
	group, err := svc.GetGroupByID(id)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Group not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch group"})
		}
		return
	}
	c.JSON(http.StatusOK, group)
}

func GetGroupWords(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group ID"})
		return
	}
	words, err := svc.GetGroupWords(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch group words"})
		return
	}
	c.JSON(http.StatusOK, words)
}

func GetGroupStudySessions(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group ID"})
		return
	}
	sessions, err := svc.GetGroupStudySessions(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch group study sessions"})
		return
	}
	c.JSON(http.StatusOK, sessions)
}

// Study Sessions Handlers
func ListStudySessions(c *gin.Context) {
	sessions, err := svc.ListStudySessions()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list study sessions"})
		return
	}
	c.JSON(http.StatusOK, sessions)
}

func GetStudySession(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study session ID"})
		return
	}
	session, err := svc.GetStudySessionByID(id)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "Study session not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch study session"})
		}
		return
	}
	c.JSON(http.StatusOK, session)
}

func GetStudySessionWords(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study session ID"})
		return
	}
	words, err := svc.GetStudySessionWords(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch study session words"})
		return
	}
	c.JSON(http.StatusOK, words)
}

// Reset Handlers
func ResetHistory(c *gin.Context) {
	err := svc.ResetHistory()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to reset history"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "History reset successfully"})
}

func FullReset(c *gin.Context) {
	err := svc.FullReset()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to perform full reset"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Full reset performed successfully"})
}

// Word Review Handler
func ReviewWord(c *gin.Context) {
	studySessionIDStr := c.Param("id")
	wordIDStr := c.Param("word_id")
	studySessionID, err := strconv.Atoi(studySessionIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study session ID"})
		return
	}
	wordID, err := strconv.Atoi(wordIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid word ID"})
		return
	}
	var req struct {
		Correct bool `json:"correct"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	err = svc.ReviewWord(studySessionID, wordID, req.Correct)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to record review"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Review recorded successfully"})
}

// CreateGroup handles POST /api/groups
func CreateGroup(c *gin.Context) {
	var req struct {
		Name string `json:"name"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	id, err := svc.CreateGroup(req.Name)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create group"})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"id": id, "name": req.Name})
}

// UpdateGroup handles PUT /api/groups/:id
func UpdateGroup(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group ID"})
		return
	}
	var req struct {
		Name string `json:"name"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	err = svc.UpdateGroup(id, req.Name)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update group"})
		return
	}
	group, err := svc.GetGroupByID(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch group after update"})
		return
	}
	c.JSON(http.StatusOK, group)
}

// DeleteGroup handles DELETE /api/groups/:id
func DeleteGroup(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group ID"})
		return
	}
	err = svc.DeleteGroup(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete group"})
		return
	}
	c.Status(http.StatusNoContent)
}

// CreateStudySession handles POST /api/study_sessions
func CreateStudySession(c *gin.Context) {
	var req struct {
		GroupID         int `json:"group_id"`
		StudyActivityID int `json:"study_activity_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	id, err := svc.CreateStudySession(req.GroupID, req.StudyActivityID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create study session"})
		return
	}
	session, err := svc.GetStudySessionByID(int(id))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch study session"})
		return
	}
	c.JSON(http.StatusCreated, session)
}

// Update CreateWord handler
func CreateWord(c *gin.Context) {
	var req struct {
		Japanese string      `json:"japanese"`
		Romaji   string      `json:"romaji"`
		English  string      `json:"english"`
		Parts    interface{} `json:"parts"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	partsStr := ""
	if req.Parts != nil {
		b, err := json.Marshal(req.Parts)
		if err == nil {
			partsStr = string(b)
		}
	}
	id, err := svc.CreateWord(req.Japanese, req.Romaji, req.English, partsStr)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create word"})
		return
	}
	word, err := svc.GetWordByID(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch created word"})
		return
	}
	c.JSON(http.StatusCreated, word)
}

func UpdateWord(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid word ID"})
		return
	}
	var req struct {
		English string `json:"english"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	if err := svc.UpdateWord(id, req.English); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "Word not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update word"})
		}
		return
	}
	word, err := svc.GetWordByID(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch updated word"})
		return
	}
	c.JSON(http.StatusOK, word)
}

func DeleteWord(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid word ID"})
		return
	}
	if err := svc.DeleteWord(id); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "Word not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete word"})
		}
		return
	}
	c.Status(http.StatusNoContent)
}

// New Handlers for Study Sessions Endpoints
func UpdateStudySession(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study session ID"})
		return
	}
	var req struct {
		StudyActivityID int `json:"study_activity_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
		return
	}
	if err := svc.UpdateStudySession(id, req.StudyActivityID); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "Study session not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update study session"})
		}
		return
	}
	session, err := svc.GetStudySessionByID(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch updated study session"})
		return
	}
	c.JSON(http.StatusOK, session)
}

func DeleteStudySession(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid study session ID"})
		return
	}
	if err := svc.DeleteStudySession(id); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusNotFound, gin.H{"error": "Study session not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete study session"})
		}
		return
	}
	c.Status(http.StatusNoContent)
}
