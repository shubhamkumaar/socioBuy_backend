# SocioBuy Backend

A social commerce platform backend built with FastAPI and Neo4j, featuring AI-powered product recommendations based on friend networks and social shopping behaviors. This backend powers the [SocioBuy Android App](https://github.com/shubhamkumaar/SocioBuy-App)

## 📱 Complete SocioBuy Ecosystem

- **🔧 Backend API** (This Repository): FastAPI + Neo4j + Gemini AI for social commerce recommendations
- **📱 Android App**: [SocioBuy Android App](https://github.com/shubhamkumaar/SocioBuy-App) - Mobile frontend 
## 🚀 Features

### Core Functionality
- **User Management**: Registration, authentication, profile management
- **Product Catalog**: Product creation, listing, and management
- **Social Shopping**: Friend connections and social influence tracking
- **Order Management**: Complete order lifecycle management
- **Smart Cart**: AI-powered product suggestions based on social networks
- **Category Management**: Product categorization and organization

### AI-Powered Recommendations
- **Social Intelligence**: Recommendations based on friend's purchases
- **Brand Affinity**: Suggestions from brands your friends prefer
- **Category Trends**: Products from categories popular in your network
- **Gemini AI Integration**: Intelligent product suggestions using Google's Gemini AI

### Social Features
- **Friend Networks**: Connect with friends and import contacts
- **Purchase Influence**: Track what your friends are buying
- **Social Recommendations**: Get suggestions based on your social circle's preferences

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: Neo4j (Graph Database)
- **Authentication**: JWT with passlib and python-jose
- **AI**: Google Gemini AI for recommendations
- **Server**: Uvicorn ASGI server
- **Configuration**: Pydantic Settings

## 📋 Prerequisites

- Python 3.8+
- Neo4j Database
- Google Gemini API Key

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shubhamkumaar/socioBuy_backend.git
   cd socioBuy_backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   NEO4J_DATABASE_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   JWT_SECRET_KEY=your_jwt_secret_key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:
- **Interactive API Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 🔗 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login

### User Management
- `GET /users/` - Get all users
- `GET /users/{user_id}` - Get user details
- `POST /users/` - Create new user
- `DELETE /users/{user_id}` - Delete user
- `POST /users/import_contacts` - Import user contacts
- `POST /users/create_order` - Create order relationship

### Products
- `GET /products/` - Get all products
- `GET /products/{product_id}` - Get product details
- `POST /products/` - Create new product

### Orders
- `POST /orders/` - Place new order
- `GET /orders/{order_id}` - Get order details
- `PUT /orders/{order_id}/status` - Update order status

### Home & Discovery
- `GET /` - Home page with personalized recommendations

### Smart Cart & AI
- `POST /ai` - Get AI-powered product suggestions based on cart

### Categories
- `POST /create_categories` - Create product category
- `GET /get_categories` - Get all categories
- `PUT /categories/{category_id}/add_products` - Add products to category

## 🗄️ Database Schema

The application uses Neo4j graph database with the following node types:

### Nodes
- **User**: User profiles with contact information
- **Product**: Product catalog with details and pricing
- **Order**: Order information and status
- **Category**: Product categorization

### Relationships
- **FRIEND**: User-to-User friendships
- **ORDERS**: User-to-Product purchase relationships
- **PLACES**: User-to-Order relationships
- **CONTAINS**: Order-to-Product and Category-to-Product relationships

## 🤖 AI Features

### Social Recommendation Engine
The AI system analyzes:
1. **Direct Product Influence**: Products your friends have ordered
2. **Brand Preferences**: Brands popular among your friends
3. **Category Trends**: Product categories trending in your network
4. **Gemini AI Suggestions**: Advanced AI recommendations using context

### How It Works
1. User adds products to cart
2. System queries friend network for purchase patterns
3. Gemini AI processes social data and generates personalized suggestions
4. Returns contextual recommendations based on social influence

## 📁 Project Structure

```
socioBuy_backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── database.py            # Neo4j database connection
├── requirements.txt       # Python dependencies
├── router/               # API route handlers
│   ├── user.py           # User management routes
│   ├── login.py          # Authentication routes
│   ├── product.py        # Product management routes
│   ├── order.py          # Order management routes
│   ├── cart.py           # Cart and AI suggestions
│   ├── home.py           # Home page and discovery
│   └── category.py       # Category management
├── models/               # Data models
│   ├── nodes.py          # Graph node models
│   ├── relations.py      # Relationship models
│   └── query.py          # Query models
├── schemas/              # Pydantic schemas
│   └── schema.py         # Request/response models
├── utils/                # Utility functions
│   ├── user.py           # User-related utilities
│   └── order.py          # Order-related utilities
└── gemini/               # AI integration
    └── gemini.py         # Gemini AI service
```

## 🔐 Authentication

The application uses JWT (JSON Web Tokens) for authentication:
- Tokens expire after configurable time (default: 30 minutes)
- Protected routes require valid JWT token
- Passwords are hashed using bcrypt

## 📱 Mobile Integration

This backend seamlessly integrates with the **SocioBuy Android App** to provide:

### Mobile-Optimized Features
- **Fast Response Times**: Optimized queries for mobile consumption
- **Offline Sync**: Support for offline cart and wishlist synchronization

- **Social Sharing**: APIs for sharing products and purchases within friend networks

### Cross-Platform Data
- **Social Graph**: Shared friend networks and social commerce data

## 🌐 Social Commerce Features

### Friend Network Analysis
- Import contacts to build friend networks
- Track friend-of-friend connections (2nd degree)
- Analyze purchase patterns across social networks

### Influence Tracking
- Monitor what products friends are buying
- Track brand preferences within friend groups
- Identify trending categories in social circles

### Smart Recommendations
- Personalized suggestions based on social data
- Context-aware AI recommendations
- Real-time friend activity integration

## 🚀 Deployment

For production deployment:

1. Set up Neo4j database cluster
2. Configure environment variables for production
3. Use a production ASGI server like Gunicorn with Uvicorn workers
4. Set up reverse proxy (Nginx)
5. Configure SSL certificates
6. Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact - Team Connect

- **Shubham Kumar**  [@shubhamkumaar](https://github.com/shubhamkumaar)
- **Kanishk Sangwan**  [@Kan1shak](https://github.com/Kan1shak)
- **Ritvik Anand**  [@RitvikAnand583](https://github.com/RitvikAnand583)
- **Sourabh Joshi**  [@Itachi2024](https://github.com/Itachi2024)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Neo4j for graph database capabilities
- Google Gemini AI for intelligent recommendations
- The Python community for amazing libraries