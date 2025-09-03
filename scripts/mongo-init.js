// MongoDB 초기화 스크립트
db = db.getSiblingDB('ketohelper');

// 컬렉션 생성 및 인덱스 설정
db.createCollection('users');
db.createCollection('recipes');
db.createCollection('restaurants');
db.createCollection('user_activities');

// 사용자 컬렉션 인덱스
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "googleId": 1 }, { unique: true, sparse: true });

// 레시피 컬렉션 인덱스
db.recipes.createIndex({ "title": "text", "description": "text", "tags": "text" });
db.recipes.createIndex({ "isKetoFriendly": 1 });
db.recipes.createIndex({ "rating": -1 });
db.recipes.createIndex({ "createdAt": -1 });

// 식당 컬렉션 인덱스
db.restaurants.createIndex({ "location": "2dsphere" });
db.restaurants.createIndex({ "name": "text", "address": "text", "category": "text" });
db.restaurants.createIndex({ "ketoScore": -1 });
db.restaurants.createIndex({ "rating": -1 });

// 사용자 활동 컬렉션 인덱스
db.user_activities.createIndex({ "userId": 1, "timestamp": -1 });
db.user_activities.createIndex({ "type": 1 });

// 샘플 데이터 삽입
print("MongoDB 초기화 완료!");
print("컬렉션과 인덱스가 생성되었습니다.");

// 샘플 레시피 데이터
db.recipes.insertMany([
  {
    title: "아보카도 베이컨 샐러드",
    description: "신선한 아보카도와 바삭한 베이컨이 만나는 완벽한 키토 샐러드",
    imageUrl: "https://via.placeholder.com/300x200",
    cookingTime: 15,
    difficulty: "easy",
    servings: 2,
    ingredients: [
      { name: "아보카도", amount: 2, unit: "개", carbs: 4 },
      { name: "베이컨", amount: 100, unit: "g", carbs: 0 },
      { name: "올리브오일", amount: 2, unit: "tbsp", carbs: 0 }
    ],
    instructions: [
      "베이컨을 바삭하게 굽습니다",
      "아보카도를 적당한 크기로 자릅니다",
      "올리브오일과 함께 섞어 완성합니다"
    ],
    nutrition: {
      calories: 380,
      carbs: 8,
      protein: 15,
      fat: 32,
      fiber: 6
    },
    tags: ["키토", "샐러드", "아보카도", "베이컨"],
    rating: 4.5,
    reviewCount: 128,
    isKetoFriendly: true,
    createdAt: new Date()
  }
]);

// 샘플 식당 데이터
db.restaurants.insertMany([
  {
    name: "키토 스테이크하우스",
    address: "서울시 강남구 테헤란로 123",
    location: {
      type: "Point",
      coordinates: [127.0276, 37.4979]
    },
    phone: "02-1234-5678",
    category: "스테이크",
    priceRange: 3,
    rating: 4.5,
    reviewCount: 128,
    operatingHours: [
      { day: "월", open: "11:00", close: "22:00" },
      { day: "화", open: "11:00", close: "22:00" },
      { day: "수", open: "11:00", close: "22:00" },
      { day: "목", open: "11:00", close: "22:00" },
      { day: "금", open: "11:00", close: "23:00" },
      { day: "토", open: "11:00", close: "23:00" },
      { day: "일", open: "11:00", close: "21:00" }
    ],
    menu: [
      {
        name: "립아이 스테이크",
        description: "프리미엄 립아이 스테이크",
        price: 45000,
        carbs: 2,
        isKetoFriendly: true,
        ketoModifications: []
      }
    ],
    ketoScore: 95,
    images: ["https://via.placeholder.com/300x200"],
    createdAt: new Date()
  }
]);

print("샘플 데이터 삽입 완료!");
