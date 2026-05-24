import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const plans = [
  {
    id: 'pay_per_use',
    name: 'Pay Per Use',
    price: '₹49',
    per: 'per screening',
    credits: '1 credit',
    color: 'border-gray-200',
    headerBg: 'bg-gray-700',
    btnColor: 'bg-gray-800 hover:bg-gray-700',
    features: [
      '1 screening credit',
      'Up to 20 resumes',
      'AI scoring 0-100',
      'Excel export',
      'No expiry'
    ]
  },
  {
    id: 'monthly',
    name: 'Monthly',
    price: '₹1,999',
    per: 'per month',
    credits: '70 credits',
    color: 'border-blue-500',
    headerBg: 'bg-blue-900',
    btnColor: 'bg-blue-900 hover:bg-blue-800',
    popular: true,
    features: [
      '70 screening credits',
      'Up to 20 resumes each',
      'AI scoring + questions',
      'Excel export',
      'Priority support',
      'Valid 30 days'
    ]
  },
  {
    id: 'annual',
    name: 'Annual',
    price: '₹19,999',
    per: 'per year',
    credits: '850 credits',
    color: 'border-purple-500',
    headerBg: 'bg-purple-800',
    btnColor: 'bg-purple-700 hover:bg-purple-600',
    features: [
      'Everything in Monthly',
      '850 screening credits',
      'Save ₹3,989/year',
      'Advanced analytics',
      'Email automation',
      'Dedicated support',
      'Valid 365 days'
    ]
  }
];

export default function Pricing() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [loading, setLoading] = useState('');
  const [error, setError] = useState('');

  const handleBuy = async (planId) => {
    if (!token) {
      navigate('/login');
      return;
    }

    setLoading(planId);
    setError('');

    try {
      // Step 1 — Create order on backend
      const res = await axios.post(
        `${API_URL}/payment/create-order?plan=${planId}&token=${token}`
      );
      const order = res.data;

      // Step 2 — Build Razorpay options
      const options = {
        key: order.razorpay_key,
        amount: order.amount,
        currency: order.currency,
        name: 'QuickHire',
        description: order.description,
        order_id: order.order_id,
        prefill: {
          name: order.user_name,
          email: order.user_email,
          contact: order.user_phone || ''
        },
        theme: {
          color: '#1B4F9E'
        },
        handler: async (response) => {
          try {
            // Step 3 — Verify payment on backend
            const verifyRes = await axios.post(
              `${API_URL}/payment/verify`,
              null,
              {
                params: {
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                  token: token
                }
              }
            );

            const result = verifyRes.data;

            // Step 4 — Update local user data
            const updatedUser = {
              ...user,
              screening_credits: result.new_credit_balance,
              plan: result.plan
            };
            localStorage.setItem('user', JSON.stringify(updatedUser));

            // Step 5 — Show success and redirect
            alert(
              `✅ Payment Successful!\n\n` +
              `Plan: ${result.plan}\n` +
              `Credits Added: ${result.credits_added}\n` +
              `New Balance: ${result.new_credit_balance} credits`
            );
            navigate('/dashboard');

          } catch (verifyErr) {
            alert(
              '⚠️ Payment received but verification failed.\n' +
              'Please contact support with your payment ID: ' +
              response.razorpay_payment_id
            );
          }
        },
        modal: {
          ondismiss: () => {
            setLoading('');
          }
        }
      };

      // Step 6 — Open Razorpay
      if (!window.Razorpay) {
        alert("Razorpay SDK failed to load. Please refresh the page or check your connection.");
        setLoading('');
        return;
      }
      const rzp = new window.Razorpay(options);

      rzp.on('payment.failed', (response) => {
        setError('Payment failed: ' + response.error.description);
        setLoading('');
      });

      rzp.open();

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Failed to create payment order. Please try again.'
      );
      setLoading('');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-blue-900 text-white px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="hover:text-blue-200 transition-colors">
            ← Dashboard
          </button>
          <span className="text-blue-300">|</span>
          <h1 className="text-xl font-bold">⚡ QuickHire Pricing</h1>
        </div>
        <div className="text-blue-200 text-sm">
          Current Credits:{' '}
          <strong className="text-white">{user.screening_credits}</strong>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto p-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-800 mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-gray-500 text-lg">
            Start free, pay only when you need more
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-6 text-center">
            ❌ {error}
          </div>
        )}

        {/* Free Plan Banner */}
        <div className="bg-gradient-to-r from-green-50 to-green-100 border border-green-200 rounded-2xl p-6 mb-8 flex justify-between items-center">
          <div>
            <h3 className="text-xl font-bold text-green-700">
              🎁 Free Plan — Currently Active
            </h3>
            <p className="text-green-600 mt-1">
              You have{' '}
              <strong>{user.screening_credits} credits</strong> remaining.
              No credit card required!
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-green-700">₹0</p>
            <p className="text-green-500 text-sm">forever free</p>
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {plans.map(plan => (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl shadow-sm border-2 ${plan.color} relative overflow-hidden transition-all hover:shadow-lg`}>

              {plan.popular && (
                <div className="absolute top-0 left-0 right-0 bg-blue-900 text-white text-center text-xs py-1.5 font-bold tracking-wide">
                  ⭐ MOST POPULAR
                </div>
              )}

              {/* Plan Header */}
              <div className={`${plan.headerBg} text-white p-6 ${plan.popular ? 'pt-8' : ''}`}>
                <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{plan.price}</span>
                </div>
                <p className="text-white text-opacity-70 text-sm mt-1">
                  {plan.per}
                </p>
                <div className="mt-3 bg-white bg-opacity-20 rounded-lg px-3 py-1.5 inline-block">
                  <span className="text-sm font-semibold">{plan.credits}</span>
                </div>
              </div>

              {/* Features */}
              <div className="p-6">
                <ul className="space-y-3 mb-6">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-green-500 font-bold mt-0.5 flex-shrink-0">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleBuy(plan.id)}
                  disabled={loading === plan.id}
                  className={`w-full py-3 ${plan.btnColor} text-white rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed`}>
                  {loading === plan.id
                    ? '⏳ Opening Payment...'
                    : `Buy ${plan.name}`}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="bg-white rounded-2xl p-8 shadow-sm mb-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-6 text-center">
            Frequently Asked Questions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                q: "What is a screening credit?",
                a: "One credit = one job screening session where you upload a JD and up to 20 resumes for AI analysis."
              },
              {
                q: "Do credits expire?",
                a: "Pay Per Use credits never expire. Monthly credits last 30 days. Annual credits last 365 days."
              },
              {
                q: "What payment methods are accepted?",
                a: "We accept UPI, Credit/Debit cards, Net Banking, and Wallets via Razorpay."
              },
              {
                q: "Can I get a refund?",
                a: "Yes! Contact support within 7 days of purchase if you are not satisfied."
              }
            ].map((faq, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-4">
                <p className="font-bold text-gray-800 mb-2">❓ {faq.q}</p>
                <p className="text-gray-600 text-sm">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Badges */}
        <div className="flex justify-center gap-8 text-gray-400 text-sm flex-wrap">
          <span>🔒 Secure Payment</span>
          <span>🏦 Razorpay Powered</span>
          <span>💳 UPI Accepted</span>
          <span>↩️ 7-Day Refund</span>
        </div>
      </div>
    </div>
  );
}