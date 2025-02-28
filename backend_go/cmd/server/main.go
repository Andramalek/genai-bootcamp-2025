package main

import (
	"log"
	"net/http"

	"backend_go/internal/handlers"
	"backend_go/internal/service"

	"github.com/gin-gonic/gin"
)

func main() {
	// Initialize the service with the SQLite database
	svc, err := service.NewService("words.db")
	if err != nil {
		log.Fatal("Error initializing service: ", err)
	}
	defer svc.Close()

	router := gin.Default()

	// Health check endpoint
	router.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "pong"})
	})

	// Register API routes and pass the service instance
	handlers.RegisterRoutes(router, svc)

	log.Println("Server is running on port 8080")
	if err := router.Run(":8080"); err != nil {
		log.Fatal("Error starting server: ", err)
	}
}
